from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    fundraising_cost_account_prefix = fields.Char(
        help="Code prefix of the accounts where the interventions are prefinanced."
    )
    fundraising_income_account_prefix = fields.Char(
        help="Code prefix of the accounts where the donations for the "
        "interventions are booked."
    )
