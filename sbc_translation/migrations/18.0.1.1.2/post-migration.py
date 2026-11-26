import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

BATCH_SIZE = 50
# Date of the migration to Odoo 18
MIGRATION_DATE = "2026-10-21"


@openupgrade.migrate()
def migrate(env, version):
    # T3623: B2S letters translated on the local platform since the migration to
    # Odoo 18 were never sent to the sponsors. Publish them now, which queues the
    # communication for each of them.
    letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("translation_status", "=", "done"),
            ("translate_done", ">=", MIGRATION_DATE),
            ("communication_id", "=", False),
        ],
        order="translate_done",
    )
    _logger.info("%s translated B2S letters to publish", len(letters))
    if letters:
        letters.with_context(force_publish=True).with_delay_sh(
            "publish_b2s_letter",
            channel="root.sbc_migration",
            priority=500,
            split=BATCH_SIZE,
            description="Publish B2S letters translated since the migration to v18",
        )
