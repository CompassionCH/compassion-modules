import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _update_reading_language(cr, sponsorship_id, lang):
    cr.execute(
        "UPDATE recurring_contract "
        "SET reading_language = %s "
        "WHERE id = %s", [lang, sponsorship_id]
    )


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    sponsorships_to_fill = env["recurring.contract"].search([
        ("reading_language", "=", False),
        ("child_id", "!=", False),
        ("state", "not in", ["terminated", "cancelled"])
    ])
    english = env.ref("child_compassion.lang_compassion_english")

    for i, sponsorship in enumerate(sponsorships_to_fill):
        _logger.info("Migrating sponsorship %s/%s", i, len(sponsorships_to_fill))
        spoken_langs = sponsorship.correspondent_id.spoken_lang_ids
        reading_lang = (spoken_langs &
                        sponsorship.child_id.correspondence_language_id) or (
            spoken_langs & english) or \
            spoken_langs.filtered(lambda l: l.lang_id.code ==
                                  sponsorship.correspondent_id.lang)
        if reading_lang:
            _update_reading_language(
                env.cr,
                sponsorship.id,
                reading_lang.id
            )
