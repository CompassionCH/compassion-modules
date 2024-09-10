from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_xmlids(
        cr,
        [
            (
                "partner_communication_compassion.child_picture",
                "child_compassion.child_picture",
            ),
            (
                "partner_communication_compassion.paperformat_child_picture",
                "child_compassion.paperformat_child_picture",
            ),
            (
                "partner_communication_compassion.report_child_picture",
                "child_compassion.report_child_picture",
            ),
        ],
    )
