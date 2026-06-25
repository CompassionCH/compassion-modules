# sbc_translation/migrations/18.0.1.1.0/post-migration.py

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Migration script to force the recalculation of translation statistics
    for existing users when updating the module.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    translators = env["translation.user"].search([])

    if not translators:
        return

    env.add_to_compute(env["translation.user"]._fields["nb_translated_letters"], translators)
    env.add_to_compute(env["translation.user"]._fields["nb_translated_letters_this_year"], translators)
    env.add_to_compute(env["translation.user"]._fields["nb_translated_letters_last_year"], translators)

    translators.flush_model([
        "nb_translated_letters",
        "nb_translated_letters_this_year",
        "nb_translated_letters_last_year"
    ])