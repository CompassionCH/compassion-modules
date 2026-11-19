import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # T3616: pages added to hold overflowing translations got a crop of the
    # letter image as background. They are not part of the scanned letter.
    pages = env["correspondence.page"].search(
        [
            ("original_page_url", "=", False),
            "|",
            ("cloudinary_original_page_url", "!=", False),
            ("cloudinary_final_page_url", "!=", False),
        ]
    )
    pages = pages.filtered(
        lambda page: page.correspondence_id.page_ids.filtered("original_page_url")
    )
    _logger.info("Remove the letter image from %s added pages", len(pages))
    pages.write(
        {"cloudinary_original_page_url": False, "cloudinary_final_page_url": False}
    )
