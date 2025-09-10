import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Restore missing pages
    letters_to_fix = env["correspondence"].search(
        [
            ("page_ids", "=", False),
            ("cloudinary_final_letter_url", "!=", False),
            ("sponsor_letter_scan", "=", False),
            ("direction", "=", "Beneficiary To Supporter"),
            ("state", "=", "Published to Global Partner"),
        ]
    )
    _logger.info(
        "Found %s letters without pages and with a cloudinary url.", len(letters_to_fix)
    )
    if not letters_to_fix:
        return

    letters_to_fix.delayable()._fix_missing_pages().set(
        priority=500, channel="root.sbc_compassion"
    ).split(100).delay()
