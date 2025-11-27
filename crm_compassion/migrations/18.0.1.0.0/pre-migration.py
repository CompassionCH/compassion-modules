# change contact types because OCA's partner_contact_in_several_companies is removed
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return
    if openupgrade.column_exists(cr, "res_partner", "contact_type"):
        cr.execute(
            "SELECT id AS partner_id, contact_id FROM res_partner "
            "WHERE contact_type = 'attached'"
        )
        partner_to_contact_values = cr.dictfetchall()
        for partner_contact in partner_to_contact_values:
            openupgrade.logged_query(
                cr,
                """
                UPDATE res_partner
                SET parent_id = %(contact_id)s, commercial_partner_id = %(contact_id)s,
                    type= 'other', active=true
                WHERE id = %(partner_id)s
            """,
                partner_contact,
            )
