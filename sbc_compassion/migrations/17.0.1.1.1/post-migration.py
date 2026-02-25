import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api
from odoo.tools import json

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files

_logger = logging.getLogger(__name__)


def _parse_object_ids(object_ids_str):
    if not object_ids_str:
        return []
    try:
        return [int(part) for part in object_ids_str.split(",") if part]
    except (TypeError, ValueError):
        return []


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_mapping_files(
        env,
        "sbc_compassion/static/mappings/",
        [
            "correspondence_mapping.json",
        ],
    )

    # Populate Cloudinary URLs for letter images
    update_letter_action = env.ref("sbc_compassion.update_letter")
    publish_messages = env["gmc.message"].search(
        [
            ("action_id", "=", update_letter_action.id),
            ("state", "=", "success"),
            ("content", "like", "Published to Global Partner"),
            ("content", "like", "http://media.ci.org/image/"),
            ("object_ids", "!=", False),
        ]
    )
    _logger.info(
        "Populating Cloudinary URLs for letter images using %d messages",
        len(publish_messages),
    )
    for message in publish_messages:
        try:
            letter_ids = _parse_object_ids(message.object_ids)
            if not letter_ids:
                continue
            letters = env["correspondence"].browse(letter_ids).exists()
            content = json.loads(message.content)
            final_url = content.get("CloudinaryFinalURL")
            original_url = content.get("CloudinaryOriginalURL")
            if letters and (final_url or original_url):
                for letter in letters:
                    letter._create_missing_pages(len(content.get("Pages", [])))
                letters.with_delay().write(
                    {
                        "cloudinary_final_letter_url": final_url,
                        "cloudinary_original_letter_url": original_url or False,
                        "sponsor_letter_scan": False,
                    }
                )
        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    # For letters not covered by the above messages, get the latest message per letter
    supporter_letters = env["correspondence"].search(
        [
            ("direction", "=", "Supporter To Beneficiary"),
            ("kit_identifier", "!=", False),
            ("cloudinary_original_letter_url", "=", False),
        ]
    )
    _logger.info(
        "Looking for Cloudinary URLs for %d supporter letters without URLs",
        len(supporter_letters),
    )
    openupgrade.logged_query(
        cr,
        """
        SELECT DISTINCT ON (m.object_ids) m.object_ids, m.content
        FROM gmc_message m
        WHERE m.action_id = %s
          AND EXISTS (
            SELECT 1
            FROM unnest(string_to_array(m.object_ids, ',')) AS obj_id
            WHERE obj_id::integer IN %s
        )
          AND m.state = 'success'
        ORDER BY m.object_ids, m.id DESC
        """,
        (update_letter_action.id, tuple(supporter_letters.ids)),
    )
    messages_data = {}
    for object_ids_str, content in cr.fetchall():
        for letter_id in _parse_object_ids(object_ids_str):
            messages_data[letter_id] = content
    for letter in supporter_letters:
        message_content_str = messages_data.get(letter.id)
        if not message_content_str:
            continue
        try:
            content = json.loads(message_content_str)
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        final_url = content.get("CloudinaryFinalURL")
        original_url = content.get("CloudinaryOriginalURL")
        if original_url:
            letter.with_delay().write(
                {
                    "cloudinary_final_letter_url": final_url or False,
                    "cloudinary_original_letter_url": original_url,
                }
            )

    # Reload correspondence templates
    openupgrade.load_data(
        env, "sbc_compassion", "data/correspondence_template_data.xml"
    )
    openupgrade.load_data(env, "sbc_compassion", "data/child_layouts.xml")
