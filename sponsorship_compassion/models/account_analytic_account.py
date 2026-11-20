##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError

COST_PLAN_PARAM = "sponsorship_compassion.cost_analytic_plan_id"


class AccountAnalyticAccount(models.Model):
    """A cost account follows the expenses of a campaign or a source (an event,
    an edition of a magazine...); their income is followed by the UTM."""

    _inherit = "account.analytic.account"

    campaign_id = fields.Many2one(
        "utm.campaign", "Campaign", index="btree_not_null", ondelete="set null"
    )
    source_id = fields.Many2one(
        "utm.source", "Source", index="btree_not_null", ondelete="set null"
    )

    @api.model
    def _create_cost_account(self, name, campaign=None, source=None):
        """Analytic account following the expenses of a campaign or a source, in
        the plan of the system parameter COST_PLAN_PARAM."""
        plan_id = self.env["ir.config_parameter"].sudo().get_param(COST_PLAN_PARAM)
        plan = self.env["account.analytic.plan"].browse(int(plan_id or 0)).exists()
        if not plan:
            raise UserError(
                _(
                    "No analytic plan is set for the expenses of the campaigns "
                    "and events."
                )
            )
        return self.create(
            {
                "name": name,
                "plan_id": plan.id,
                "campaign_id": campaign and campaign.id,
                "source_id": source and source.id,
            }
        )

    def _action_open(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.account",
            "view_mode": "list,form" if len(self) > 1 else "form",
            "res_id": self.id if len(self) == 1 else False,
            "domain": [("id", "in", self.ids)],
            "name": _("Expenses"),
        }
