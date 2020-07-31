import json

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return
    # Restore templates of sent letters to GMC
    default_template = env.ref("sbc_compassion.default_template")
    wrong_letters = env["correspondence"].search([
        ("direction", "=", "Supporter To Beneficiary"),
        ("kit_identifier", "!=", False),
        ("store_letter_image", "=", False),
        ("template_id", "=", default_template.id)
    ])
    # We arbitrarily put worldmap web as template as we have no clue which was used.
    wrong_letters.write({"template_id": 38})
