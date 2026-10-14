##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models
from odoo.tools import SQL


class AnalyticAccount(models.Model):
    _inherit = "account.analytic.line"

    @api.model_create_multi
    def create(self, vals_list):
        # Force negative amount to make sure it's accounted in the events' expenses
        if self.env.context.get("expense_from_event"):
            for vals in vals_list:
                if vals.get("amount", 0) > 0:
                    vals["amount"] = -vals["amount"]
        lines = super().create(vals_list)
        lines._recompute_event_expenses(lines._get_events())
        return lines

    def write(self, vals):
        if not self._event_expense_fields().intersection(vals):
            return super().write(vals)
        events = self._get_events()
        res = super().write(vals)
        self._recompute_event_expenses(events | self._get_events())
        return res

    def unlink(self):
        events = self._get_events()
        res = super().unlink()
        self._recompute_event_expenses(events)
        return res

    def _event_expense_fields(self):
        return {"amount", "auto_account_id", *self._get_plan_fnames()}

    def _get_events(self):
        """Events whose analytic account is on these lines, in any plan column."""
        accounts = self.env["account.analytic.account"]
        for fname in self._get_plan_fnames():
            accounts |= self.mapped(fname)
        if not accounts:
            return self.env["crm.event.compassion"]
        return (
            self.env["crm.event.compassion"]
            .sudo()
            .search([("analytic_id", "in", accounts.ids)])
        )

    def _recompute_event_expenses(self, events):
        if events:
            events.invalidate_recordset(["expense_line_ids"])
            self.env.add_to_compute(events._fields["total_expense"], events)
            events.modified(["total_expense"])

    @api.model
    def _get_expense_totals(self, accounts):
        """Sum of the negative lines of each account, in any plan column. A
        line holding the same account in two columns is counted once."""
        if not accounts:
            return {}
        fnames = self._get_plan_fnames()
        self.flush_model([*fnames, "amount"])
        columns = [SQL.identifier("line", fname) for fname in fnames]
        self.env.cr.execute(
            SQL(
                """
                SELECT acc.id, SUM(line.amount)
                  FROM account_analytic_line line
                 CROSS JOIN LATERAL (
                       SELECT DISTINCT unnest(ARRAY[%(columns)s])
                       ) AS acc(id)
                 WHERE (%(in_any_column)s)
                   AND line.amount < 0
                   AND acc.id = ANY(%(ids)s)
                 GROUP BY acc.id
                """,
                columns=SQL(", ").join(columns),
                in_any_column=SQL(" OR ").join(
                    SQL("%s = ANY(%s)", column, accounts.ids) for column in columns
                ),
                ids=accounts.ids,
            )
        )
        return dict(self.env.cr.fetchall())
