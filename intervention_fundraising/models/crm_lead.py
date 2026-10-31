from odoo import api, fields, models


class CrmLead(models.Model):
    """A pledge is an opportunity linked to an intervention: asked while open,
    pledged once won. What the donor gives for the intervention since the
    pledge is received."""

    _inherit = "crm.lead"

    intervention_id = fields.Many2one(
        "compassion.intervention",
        "Intervention",
        index="btree_not_null",
        tracking=True,
        domain=[("state", "in", ["committed", "active", "on_hold", "sla"])],
    )
    pledge_received = fields.Monetary(
        "Received",
        currency_field="company_currency",
        compute="_compute_pledge_received",
    )
    pledge_remaining = fields.Monetary(
        "Not received yet",
        currency_field="company_currency",
        compute="_compute_pledge_received",
    )

    @api.depends(
        "intervention_id", "partner_id", "stage_id", "date_closed", "expected_revenue"
    )
    def _compute_pledge_received(self):
        for lead in self:
            received = 0
            if lead.intervention_id and lead.partner_id and lead.stage_id.is_won:
                since = lead.date_closed or lead.create_date
                lines = self.env["intervention.fundraising.line"].search(
                    [
                        ("intervention_id", "=", lead.intervention_id.id),
                        ("partner_id", "=", lead.partner_id.commercial_partner_id.id),
                        ("kind", "=", "income"),
                        ("date", ">=", since.date() if since else False),
                    ]
                )
                received = sum(lines.mapped("amount"))
            lead.pledge_received = received
            lead.pledge_remaining = (
                max(lead.expected_revenue - received, 0) if lead.stage_id.is_won else 0
            )

    @api.model_create_multi
    def create(self, vals_list):
        team = self.env.ref(
            "intervention_fundraising.crm_team_fundraising", raise_if_not_found=False
        )
        for vals in vals_list:
            if vals.get("intervention_id") and team and not vals.get("team_id"):
                vals["team_id"] = team.id
            if not vals.get("name") and vals.get("intervention_id"):
                intervention = self.env["compassion.intervention"].browse(
                    vals["intervention_id"]
                )
                partner = self.env["res.partner"].browse(vals.get("partner_id"))
                vals["name"] = " - ".join(
                    filter(None, [partner.name, intervention.name])
                )
        return super().create(vals_list)
