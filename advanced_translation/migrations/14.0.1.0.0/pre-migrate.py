from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "child_switzerland.lang_compassion_german",
                "advanced_translation.lang_compassion_german",
            ),
            (
                "child_switzerland.lang_compassion_italian",
                "advanced_translation.lang_compassion_italian",
            ),
        ],
    )
