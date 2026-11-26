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
        lines._get_events()._recompute_expenses()
        return lines

    def write(self, vals):
        if not self._event_expense_fields().intersection(vals):
            return super().write(vals)
        events = self._get_events()
        res = super().write(vals)
        (events | self._get_events())._recompute_expenses()
        return res

    def unlink(self):
        events = self._get_events()
        res = super().unlink()
        events._recompute_expenses()
        return res

    def _event_expense_fields(self):
        return {"amount", "auto_account_id", *self._get_plan_fnames()}

    def _get_events(self):
        """Events whose analytic account is on these lines, in any plan column."""
        accounts = self.env["account.analytic.account"].union(
            *(self.mapped(fname) for fname in self._get_plan_fnames())
        )
        return (
            self.env["crm.event.compassion"]
            .sudo()
            .search([("analytic_id", "in", accounts.ids)])
        )
