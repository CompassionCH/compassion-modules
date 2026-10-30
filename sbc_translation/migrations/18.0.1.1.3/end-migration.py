import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # T3616: spread the translation of the letters printing it on the original
    # image, like new translations are. It moves the text out of pages without
    # a translation box (B2S L4/L6) and fits it in the resized boxes.
    # End script: report_needs_final_text is overridden in later modules.
    letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("translation_status", "=", "done"),
            ("src_translation_lang_id", "!=", False),
        ]
    )
    letters = letters.filtered("report_needs_final_text")
    _logger.info("Spreading the translation of %s B2S letters", len(letters))
    for letter in letters:
        letter.spread_text_to_pages(["translated_text"])
