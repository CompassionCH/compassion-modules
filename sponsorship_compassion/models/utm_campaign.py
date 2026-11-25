##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class UtmCampaign(models.Model):
    _inherit = "utm.campaign"

    cost_account_ids = fields.One2many(
        "account.analytic.account", "campaign_id", "Cost accounts"
    )

    def action_track_expenses(self):
        """Open the cost account of the campaign, created when it has none."""
        self.ensure_one()
        accounts = self.cost_account_ids or self.env[
            "account.analytic.account"
        ]._create_cost_account(self.title or self.name, campaign=self)
        return accounts._action_open()
