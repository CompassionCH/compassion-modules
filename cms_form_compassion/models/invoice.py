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

    auto_cancel_no_transaction = fields.Boolean(
        default=False, help='If true, cancel the invoice if the linked payment '
        'transaction is cancelled'
    )

    auto_cancel_date = fields.Datetime(
        string="Auto cancel date",
        help="Date at which the invoice should be canceled automatically via Automated Actions",
        default=False,
        invisible=True,
        readonly=True,
    )

    @api.multi
    def auto_cancel(self):
        invoices = self.filtered(lambda i: i.state == "draft")
        invoices.write({"auto_cancel_date": False})
        invoices.action_invoice_cancel()
