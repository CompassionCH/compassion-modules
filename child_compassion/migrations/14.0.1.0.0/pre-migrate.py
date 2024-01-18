from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "partner_communication_switzerland.child_him_en",
                "child_compassion.child_him",
            ),
            ("child_switzerland.child_he_en", "child_compassion.child_he"),
            ("child_switzerland.child_his_en", "child_compassion.child_his"),
            (
                "partner_communication_switzerland.child_child_en",
                "child_compassion.child_child",
            ),
        ],
    )
