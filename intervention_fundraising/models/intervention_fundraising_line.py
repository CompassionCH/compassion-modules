from odoo import fields, models, tools

# Posted journal items on the analytic account of an intervention, split by
# analytic distribution, on the cost or income accounts of the company.
# The condition on regexp_split_to_array uses the GIN index of
# account_move_line on the keys of analytic_distribution.
LINES_QUERY = r"""
    SELECT ml.id AS move_line_id, i.id AS intervention_id, ml.company_id,
           c.currency_id, ml.move_id, ml.account_id, ml.date,
           p.commercial_partner_id AS partner_id,
           CASE WHEN a.is_cost THEN 'cost' ELSE 'income' END::text AS kind,
           ml.balance * d.value::numeric / 100
               * CASE WHEN a.is_cost THEN 1 ELSE -1 END AS amount
    FROM account_move_line ml
    JOIN res_company c ON c.id = ml.company_id
    JOIN account_account gl ON gl.id = ml.account_id
    CROSS JOIN LATERAL (
        SELECT code LIKE nullif(c.fundraising_cost_account_prefix, '') || '%'
                   AS is_cost,
               code LIKE nullif(c.fundraising_income_account_prefix, '') || '%'
                   AS is_income
        FROM (SELECT gl.code_store->>ml.company_id::text AS code) gl_code
    ) a
    LEFT JOIN res_partner p ON p.id = ml.partner_id
    CROSS JOIN LATERAL jsonb_each_text(ml.analytic_distribution) d
    CROSS JOIN LATERAL regexp_split_to_table(d.key, ',') kk
    JOIN compassion_intervention i ON i.analytic_account_id = kk::integer
    WHERE ml.parent_state = 'posted'
      AND regexp_split_to_array(
            jsonb_path_query_array(ml.analytic_distribution,
                                   '$.keyvalue()."key"')::text, '\D+')
          && ARRAY(SELECT analytic_account_id::text FROM compassion_intervention
                   WHERE analytic_account_id IS NOT NULL)
      AND (a.is_cost OR a.is_income)
"""

# The lines are few (the analytic accounts of the interventions are seldom
# used). In a function, the planner sees them as a small table: inlined in the
# views, its estimates on account_move_line make it compile the queries (JIT)
# for seconds.
LINES_FUNCTION = f"""
    CREATE OR REPLACE FUNCTION intervention_fundraising_lines()
    RETURNS TABLE (
        move_line_id integer, intervention_id integer, company_id integer,
        currency_id integer, move_id integer, account_id integer, date date,
        partner_id integer, kind text, amount numeric
    )
    LANGUAGE sql STABLE ROWS 1000 SET jit = off AS $$
        {LINES_QUERY}
    $$
"""


class InterventionFundraisingLine(models.Model):
    _name = "intervention.fundraising.line"
    _description = "Intervention cost or donation"
    _auto = False
    _order = "date desc"

    intervention_id = fields.Many2one("compassion.intervention", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    move_line_id = fields.Many2one("account.move.line", readonly=True)
    move_id = fields.Many2one("account.move", readonly=True)
    account_id = fields.Many2one("account.account", readonly=True)
    date = fields.Date(readonly=True)
    partner_id = fields.Many2one("res.partner", "Donor", readonly=True)
    kind = fields.Selection(
        [("cost", "Prefinancing"), ("income", "Donation")], readonly=True
    )
    amount = fields.Monetary(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, "intervention_fundraising_report")
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("DROP FUNCTION IF EXISTS intervention_fundraising_lines()")
        self.env.cr.execute(LINES_FUNCTION)
        self.env.cr.execute(
            f"""CREATE VIEW {self._table} AS (
                SELECT l.move_line_id::bigint * 1000000 + l.intervention_id AS id,
                       l.*
                FROM intervention_fundraising_lines() l
            )"""
        )
