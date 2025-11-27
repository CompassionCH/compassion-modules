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
        return super().create(vals_list)
