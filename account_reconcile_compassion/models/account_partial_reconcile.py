##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class AccountPartialReconcile(models.Model):
    """
    The method below add the functionality to set a default analytic account
    when there is none.
    """

    _inherit = "account.partial.reconcile"

    def _fix_multiple_exchange_rates_diff(
            self, amls_to_fix, amount_diff, diff_in_currency, currency, move
    ):
        analytic_account_id = (
            self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                "account_reconcile_compassion.currency_exchange_analytic_account"
            )
        )

        return super(
            AccountPartialReconcile,
            self.with_context(default_analytic_account_id=analytic_account_id),
        )._fix_multiple_exchange_rates_diff(
            amls_to_fix, amount_diff, diff_in_currency, currency, move
        )
