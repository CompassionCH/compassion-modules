from odoo import api, fields, models

FUNDRAISING_STATES = [
    ("open", "Open"),
    ("funded", "Fully funded"),
    ("closed", "Closed"),
]
FUNDRAISING_PRIORITIES = [
    ("0", "Normal"),
    ("1", "Important"),
    ("2", "Urgent"),
]
FUNDING_LEVELS = [
    ("fully", "Fully funded"),
    ("partially", "Partially funded"),
    ("not", "Not funded"),
    ("unknown", "Unknown"),
]
COST_SOURCES = [
    ("prefinanced", "Prefinanced"),
    ("estimated", "Estimated (USD)"),
    ("unknown", "Unknown"),
]


class CompassionIntervention(models.Model):
    _inherit = "compassion.intervention"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company currency"
    )
    fundraiser_id = fields.Many2one(
        "res.users",
        "Fundraiser",
        domain=[("share", "=", False)],
        tracking=True,
    )
    fundraising_state = fields.Selection(
        FUNDRAISING_STATES, default="open", required=True, tracking=True
    )
    fundraising_closed_by = fields.Many2one("res.users", readonly=True)
    fundraising_closed_date = fields.Date(readonly=True)
    fundraising_priority = fields.Selection(
        FUNDRAISING_PRIORITIES, "Fundraising priority", default="0", tracking=True
    )
    fundraising_deadline = fields.Date(
        tracking=True, help="Date by which the funds are needed"
    )
    donor_type_ids = fields.Many2many(
        "intervention.donor.type", string="Suited donor types"
    )
    earmarking = fields.Selection(
        [("earmarked", "Earmarked"), ("free", "Not earmarked")],
        help="Empty when unknown",
    )
    benchmark_amount = fields.Monetary(
        currency_field="company_currency_id",
        help="Typical gift amount to ask a donor for",
    )
    clear_ask = fields.Text(help="What we ask the donors for, in one sentence")
    impact_summary = fields.Text(help="Measurable impact of the intervention")
    impact_calculation = fields.Text(
        help="Result of the impact calculation tool (to come)"
    )
    fundraising_stories = fields.Html("Stories")
    pledge_ids = fields.One2many("crm.lead", "intervention_id", "Pledges")
    pledge_count = fields.Integer(compute="_compute_pledge_count")
    fundraising_team_id = fields.Many2one(
        "crm.team", compute="_compute_fundraising_team_id"
    )

    # Funding, from the report (in the company currency)
    funding_cost = fields.Monetary(
        "Cost", currency_field="company_currency_id", compute="_compute_funding"
    )
    funding_cost_source = fields.Selection(
        COST_SOURCES,
        "Cost source",
        compute="_compute_funding",
    )
    funding_received = fields.Monetary(
        "Received", currency_field="company_currency_id", compute="_compute_funding"
    )
    funding_pledged = fields.Monetary(
        "Pledged, not received",
        currency_field="company_currency_id",
        compute="_compute_funding",
    )
    funding_in_discussion = fields.Monetary(
        "In discussion",
        currency_field="company_currency_id",
        compute="_compute_funding",
    )
    funding_gap = fields.Monetary(
        "Funding gap", currency_field="company_currency_id", compute="_compute_funding"
    )
    funding_coverage = fields.Float("Coverage (%)", compute="_compute_funding")
    funding_level = fields.Selection(
        FUNDING_LEVELS,
        compute="_compute_funding",
    )
    funding_usd_rate_date = fields.Date("USD rate of", compute="_compute_funding")

    @api.depends("pledge_ids")
    def _compute_pledge_count(self):
        for intervention in self:
            intervention.pledge_count = len(intervention.pledge_ids)

    def _compute_fundraising_team_id(self):
        self.fundraising_team_id = self.env.ref(
            "intervention_fundraising.crm_team_fundraising", raise_if_not_found=False
        )

    def _compute_funding(self):
        reports = {
            report.id: report
            for report in self.env["intervention.fundraising.report"]
            .sudo()
            .search([("id", "in", self.ids)])
        }
        for intervention in self:
            report = reports.get(intervention.id)
            intervention.funding_cost = report.cost if report else False
            intervention.funding_cost_source = report.cost_source if report else False
            intervention.funding_received = report.received if report else 0
            intervention.funding_pledged = report.pledged if report else 0
            intervention.funding_in_discussion = report.in_discussion if report else 0
            intervention.funding_gap = report.gap if report else False
            intervention.funding_coverage = report.coverage if report else False
            intervention.funding_level = report.funding_level if report else False
            intervention.funding_usd_rate_date = (
                report.usd_rate_date if report else False
            )

    def action_close_fundraising(self):
        self.write(
            {
                "fundraising_state": "closed",
                "fundraising_closed_by": self.env.uid,
                "fundraising_closed_date": fields.Date.context_today(self),
            }
        )

    def action_fundraising_funded(self):
        self.write(
            {
                "fundraising_state": "funded",
                "fundraising_closed_by": self.env.uid,
                "fundraising_closed_date": fields.Date.context_today(self),
            }
        )

    def action_reopen_fundraising(self):
        self.write(
            {
                "fundraising_state": "open",
                "fundraising_closed_by": False,
                "fundraising_closed_date": False,
            }
        )

    def action_open_pledges(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "intervention_fundraising.action_intervention_pledges"
        )
        action["domain"] = [("intervention_id", "=", self.id)]
        action["context"] = {
            "default_intervention_id": self.id,
            "default_type": "opportunity",
            "default_team_id": self.env.ref(
                "intervention_fundraising.crm_team_fundraising"
            ).id,
        }
        return action

    def action_open_donations(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "intervention_fundraising.action_intervention_fundraising_line"
        )
        action["domain"] = [("intervention_id", "=", self.id)]
        action["context"] = {"search_default_donations": 1}
        return action
