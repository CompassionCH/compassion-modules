# Email aliases table is removed, we convert them to Other Adresses
from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not openupgrade.table_exists(cr, "res_partner_email"):
        return
    cr.execute("""SELECT partner_id, email FROM res_partner_email""")
    env = api.Environment(cr, SUPERUSER_ID, {})
    for alias_data in cr.dictfetchall():
        env["res.partner"].create(
            {
                "parent_id": alias_data["partner_id"],
                "type": "other",
                "email": alias_data["email"],
            }
        )
