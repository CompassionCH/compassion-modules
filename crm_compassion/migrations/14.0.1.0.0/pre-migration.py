from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_fields(
        cr, [("recurring.contract", "recurring_contract", "user_id", "ambassador_id")]
    )
