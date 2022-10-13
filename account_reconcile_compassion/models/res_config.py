##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class AccountConfigSettings(models.TransientModel):
    """
    Add the possibility to configure a default analytic account in
    Compassion settings to be use for file upload when there is
    currency exchange.
    """

    _inherit = "res.config.settings"

    currency_exchange_analytic_account = fields.Many2one(
        "account.analytic.account", readonly=False
    )

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "account_reconcile_compassion.currency_exchange_analytic_account",
            str(self.currency_exchange_analytic_account.id),
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res["currency_exchange_analytic_account"] = int(
            param_obj.get_param(
                "account_reconcile_compassion.currency_exchange_analytic_account"
            )
        )
        return res
