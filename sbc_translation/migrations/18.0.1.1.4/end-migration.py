import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # T3616: the extra scanned pages of a letter no longer have a text box.
    # Move the translation printed on them to the next box.
    env.cr.execute(
        """
        WITH template_pages AS (
            SELECT template_id, count(*) AS total
            FROM correspondence_template_page GROUP BY template_id
        ), scanned_pages AS (
            SELECT correspondence_id, count(*) AS total
            FROM correspondence_page
            WHERE original_page_url IS NOT NULL GROUP BY correspondence_id
        )
        SELECT c.id FROM correspondence c
        JOIN scanned_pages s ON s.correspondence_id = c.id
        JOIN template_pages t ON t.template_id = c.template_id
        WHERE c.direction = 'Beneficiary To Supporter'
          AND c.translation_status = 'done'
          AND c.src_translation_lang_id IS NOT NULL
          AND s.total > t.total
        """
    )
    letters = env["correspondence"].browse([row[0] for row in env.cr.fetchall()])
    _logger.info("Queue the spreading of the translation of %s letters", len(letters))
    if letters:
        letters.with_delay_sh(
            "spread_translation",
            channel="root.sbc_migration",
            priority=500,
            split=200,
            description="Move translations out of extra scanned pages",
        )
