from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api
from odoo.tools import json

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_mapping_files(
        env,
        "sbc_compassion/static/mappings/",
        [
            "correspondence_mapping.json",
        ],
    )
    # Remove the letter attachment in batch jobs of 100 letters
    offset = 0
    b2s_letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("sponsor_letter_scan", "!=", False),
        ],
        limit=100,
        offset=offset,
    )
    while b2s_letters:
        b2s_letters.with_delay().write({"sponsor_letter_scan": False})
        offset += 100
        b2s_letters = env["correspondence"].search(
            [
                ("direction", "=", "Beneficiary To Supporter"),
                ("sponsor_letter_scan", "!=", False),
            ],
            limit=100,
            offset=offset,
        )

    # Populate Cloudinary URLs for letter images
    update_letter_action = env.ref("sbc_compassion.update_letter")
    publish_messages = env["gmc.message"].search(
        [
            ("action_id", "=", update_letter_action.id),
            ("state", "=", "success"),
            ("content", "like", "Published to Global Partner"),
            ("content", "like", "http://media.ci.org/image/"),
        ]
    )
    for message in publish_messages:
        letter = env["correspondence"].browse(int(message.object_ids))
        content = json.loads(message.content)
        final_url = content.get("CloudinaryFinalURL")
        original_url = content.get("CloudinaryOriginalURL")
        if final_url and letter.exists():
            letter.with_delay().write(
                {
                    "cloudinary_final_letter_url": final_url,
                    "cloudinary_original_letter_url": original_url,
                }
            )

    # Reload correspondence templates
    openupgrade.load_data(
        env, "sbc_compassion", "data/correspondence_template_data.xml"
    )
    openupgrade.load_data(env, "sbc_compassion", "data/child_layouts.xml")
