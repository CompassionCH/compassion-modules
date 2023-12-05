##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Robin Berguerand <robin.berguerand@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    auto_cancel_date = fields.Datetime(
        string="Auto cancel date",
        help="Date after which the invoice should be canceled automatically via "
             "scheduled action",
    )

    @api.model
    def auto_cancel(self):
        invoices = self.search([
            ("auto_cancel_date", "<=", fields.Datetime.now()),
            ("state", "in", ["draft", "open"])
        ], limit=100)
        invoices.action_invoice_cancel()
        return True
