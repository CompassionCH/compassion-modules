from openupgradelib import openupgrade

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


@openupgrade.migrate()
def migrate(env, version):
    load_mapping_files(
        env,
        "sbc_compassion/static/mappings/",
        [
            "correspondence_mapping.json",
        ],
    )
    # Remove the letter attachment in batch jobs of 100 letters
    offset = 0
    b2s_letters = env["correspondence"].search(
        [
            ("direction", "=", "Beneficiary To Supporter"),
            ("sponsor_letter_scan", "!=", False),
        ],
        limit=100,
        offset=offset,
    )
    while b2s_letters:
        b2s_letters.with_delay().write({"sponsor_letter_scan": False})
        offset += 100
        b2s_letters = env["correspondence"].search(
            [
                ("direction", "=", "Beneficiary To Supporter"),
                ("sponsor_letter_scan", "!=", False),
            ],
            limit=100,
            offset=offset,
        )

    # Reload correspondence templates
    openupgrade.load_data(
        env, "sbc_compassion", "data/correspondence_template_data.xml"
    )
    openupgrade.load_data(env, "sbc_compassion", "data/child_layouts.xml")
