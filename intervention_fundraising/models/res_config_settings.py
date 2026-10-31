from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fundraising_cost_account_prefix = fields.Char(
        related="company_id.fundraising_cost_account_prefix", readonly=False
    )
    fundraising_income_account_prefix = fields.Char(
        related="company_id.fundraising_income_account_prefix", readonly=False
    )
