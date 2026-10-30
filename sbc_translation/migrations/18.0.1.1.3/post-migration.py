import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The B2S boxes are noupdate data: set the positions matching the templates.
TEXT_BOXES = {
    "sbc_compassion.b2s_l2_box_2": {"height": 46},
    "sbc_compassion.b2s_l3_box_1": {"height": 64.5},
    "sbc_compassion.b2s_l3_box_2": {"y_min": 7, "height": 79},
    "sbc_compassion.b2s_l4_box_1": {
        "x_min": 8.14,
        "y_min": 5,
        "width": 82.33,
        "height": 35.41,
    },
}


@openupgrade.migrate()
def migrate(env, version):
    for xmlid, vals in TEXT_BOXES.items():
        box = env.ref(xmlid, raise_if_not_found=False)
        if box:
            box.write(vals)

    # T3616: on B2S L4/L6, page 1 has no translation box, so the local
    # translation saved there was never printed. Move it to the next box.
    templates = env.ref("sbc_compassion.b2s_l4") | env.ref("sbc_compassion.b2s_l6")
    letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("translation_status", "=", "done"),
            ("src_translation_lang_id", "!=", False),
            ("template_id", "in", templates.ids),
        ]
    )
    to_fix = letters.filtered(
        lambda letter: any(
            paragraph.translated_text and not paragraph.get_text_box("translated_text")
            for paragraph in letter.page_ids.paragraph_ids
        )
    )
    _logger.info("Moving the translation to its box on %s B2S letters", len(to_fix))
    for letter in to_fix:
        letter.spread_text_to_pages(["translated_text"])
