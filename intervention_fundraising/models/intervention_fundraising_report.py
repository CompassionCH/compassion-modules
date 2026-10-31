from odoo import fields, models, tools

from .compassion_intervention import (
    COST_SOURCES,
    FUNDING_LEVELS,
    FUNDRAISING_PRIORITIES,
    FUNDRAISING_STATES,
)


class InterventionFundraisingReport(models.Model):
    """Funding of the interventions, in the currency of their company.

    - cost: prefinanced amount on the cost accounts, otherwise the commitment
      (in USD) at the latest rate; empty (unknown) without either of them;
    - received: donations on the income accounts;
    - pledged: won pledges not yet received, per donor: what the donor gave
      for the intervention since the pledge is deducted;
    - in_discussion: open pledges not yet won;
    - gap: cost - received - pledged.
    """

    _name = "intervention.fundraising.report"
    _description = "Intervention funding"
    _auto = False
    _order = "fundraising_deadline, gap desc nulls last"
    _rec_name = "intervention_id"

    intervention_id = fields.Many2one("compassion.intervention", readonly=True)
    intervention_code = fields.Char("Intervention ID", readonly=True)
    name = fields.Char(readonly=True)
    state = fields.Selection(
        lambda self: self.env["compassion.intervention"]._fields["state"].selection,
        readonly=True,
    )
    company_id = fields.Many2one("res.company", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    field_office_id = fields.Many2one("compassion.field.office", readonly=True)
    country_id = fields.Many2one("res.country", readonly=True)
    category_id = fields.Many2one("compassion.intervention.category", readonly=True)
    user_id = fields.Many2one("res.users", "Primary owner", readonly=True)
    fundraiser_id = fields.Many2one("res.users", "Fundraiser", readonly=True)
    fundraising_state = fields.Selection(FUNDRAISING_STATES, readonly=True)
    fundraising_priority = fields.Selection(
        FUNDRAISING_PRIORITIES, "Priority", readonly=True
    )
    fundraising_deadline = fields.Date("Deadline", readonly=True)
    fundraising_closed_date = fields.Date("Fundraising closed on", readonly=True)
    planned_end_date = fields.Date(readonly=True)
    commitment_amount = fields.Float("Commitment (USD)", readonly=True)
    usd_rate_date = fields.Date("USD rate of", readonly=True)
    cost_source = fields.Selection(COST_SOURCES, readonly=True)
    cost = fields.Monetary(readonly=True)
    received = fields.Monetary(readonly=True)
    pledged = fields.Monetary("Pledged, not received", readonly=True)
    in_discussion = fields.Monetary(readonly=True)
    gap = fields.Monetary("Funding gap", readonly=True)
    coverage = fields.Float("Coverage (%)", readonly=True, aggregator="avg")
    funding_level = fields.Selection(FUNDING_LEVELS, readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""CREATE VIEW {self._table} AS (
            WITH line AS (SELECT * FROM intervention_fundraising_line),
            totals AS (
                SELECT intervention_id,
                       sum(amount) FILTER (WHERE kind = 'cost') AS prefinanced,
                       coalesce(sum(amount) FILTER (WHERE kind = 'income'), 0)
                           AS received
                FROM line GROUP BY intervention_id
            ),
            pledge AS (
                SELECT l.intervention_id, p.commercial_partner_id AS partner_id,
                       sum(l.expected_revenue) AS amount,
                       min(coalesce(l.date_closed, l.create_date))::date AS date
                FROM crm_lead l
                JOIN crm_stage s ON s.id = l.stage_id
                JOIN res_partner p ON p.id = l.partner_id
                WHERE l.intervention_id IS NOT NULL AND l.active AND s.is_won
                GROUP BY 1, 2
            ),
            pledge_received AS (
                SELECT pledge.intervention_id, pledge.partner_id,
                       sum(line.amount) AS amount
                FROM pledge
                JOIN line ON line.intervention_id = pledge.intervention_id
                         AND line.partner_id = pledge.partner_id
                         AND line.kind = 'income' AND line.date >= pledge.date
                GROUP BY 1, 2
            ),
            pledged AS (
                SELECT p.intervention_id,
                       sum(greatest(p.amount - coalesce(r.amount, 0), 0)) AS amount
                FROM pledge p
                LEFT JOIN pledge_received r
                       ON r.intervention_id = p.intervention_id
                      AND r.partner_id = p.partner_id
                GROUP BY 1
            ),
            discussion AS (
                SELECT l.intervention_id, sum(l.expected_revenue) AS amount
                FROM crm_lead l
                JOIN crm_stage s ON s.id = l.stage_id
                WHERE l.intervention_id IS NOT NULL AND l.active
                  AND NOT coalesce(s.is_won, false)
                GROUP BY 1
            ),
            civ AS (
                SELECT i.*, c.currency_id, t.prefinanced,
                       coalesce(t.received, 0) AS received,
                       coalesce(pd.amount, 0) AS pledged,
                       coalesce(ds.amount, 0) AS in_discussion,
                       usd.name AS usd_rate_date,
                       nullif(i.commitment_amount, 0)
                           * coalesce(cur.rate, 1) / usd.rate AS estimate
                FROM compassion_intervention i
                JOIN res_company c ON c.id = i.company_id
                LEFT JOIN totals t ON t.intervention_id = i.id
                LEFT JOIN pledged pd ON pd.intervention_id = i.id
                LEFT JOIN discussion ds ON ds.intervention_id = i.id
                LEFT JOIN LATERAL (
                    SELECT r.name, r.rate FROM res_currency_rate r
                    JOIN res_currency x ON x.id = r.currency_id AND x.name = 'USD'
                    WHERE r.company_id = i.company_id OR r.company_id IS NULL
                    ORDER BY r.name DESC, r.company_id NULLS LAST LIMIT 1
                ) usd ON true
                LEFT JOIN LATERAL (
                    SELECT r.rate FROM res_currency_rate r
                    WHERE r.currency_id = c.currency_id
                      AND (r.company_id = i.company_id OR r.company_id IS NULL)
                    ORDER BY r.name DESC, r.company_id NULLS LAST LIMIT 1
                ) cur ON true
            ),
            funding AS (
                SELECT civ.*,
                       CASE WHEN prefinanced > 0 THEN prefinanced
                            ELSE estimate END AS cost
                FROM civ
            )
            SELECT f.id, f.id AS intervention_id,
                   f.intervention_id AS intervention_code, f.name, f.state,
                   f.company_id, f.currency_id, f.field_office_id,
                   fo.country_id, f.category_id, f.user_id, f.fundraiser_id,
                   f.fundraising_state, f.fundraising_priority,
                   f.fundraising_deadline, f.fundraising_closed_date,
                   f.planned_end_date,
                   f.commitment_amount, f.usd_rate_date,
                   CASE WHEN f.prefinanced > 0 THEN 'prefinanced'
                        WHEN f.estimate IS NOT NULL THEN 'estimated'
                        ELSE 'unknown' END AS cost_source,
                   f.cost, f.received, f.pledged, f.in_discussion,
                   f.cost - f.received - f.pledged AS gap,
                   round(((f.received + f.pledged) / nullif(f.cost, 0) * 100)::numeric, 1)
                       AS coverage,
                   CASE WHEN f.cost IS NULL THEN 'unknown'
                        WHEN f.received + f.pledged >= f.cost THEN 'fully'
                        WHEN f.received + f.pledged > 0 THEN 'partially'
                        ELSE 'not' END AS funding_level
            FROM funding f
            LEFT JOIN compassion_field_office fo ON fo.id = f.field_office_id
            )"""
        )

    def action_open_intervention(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "compassion.intervention",
            "res_id": self.intervention_id.id,
            "view_mode": "form",
            "target": "current",
        }
