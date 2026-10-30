import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

BATCH_SIZE = 200


@openupgrade.migrate()
def migrate(env, version):
    # T3616: spread the translation of the letters printing it on the original
    # image, like new translations are. It moves the text out of pages without
    # a translation box (B2S L4/L6) and fits it in the resized boxes.
    # Done in jobs to keep the upgrade short. End script: the boxes of
    # sbc_compassion are updated before.
    letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("translation_status", "=", "done"),
            ("src_translation_lang_id", "!=", False),
        ]
    )
    _logger.info("Queue the spreading of the translation of %s letters", len(letters))
    if letters:
        letters.with_delay_sh(
            "spread_translation",
            channel="root.sbc_migration",
            priority=500,
            split=BATCH_SIZE,
            description="Fit the local translation of B2S letters in their boxes",
        )
