##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Robin Berguerand <robin.berguerand@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _set_transaction_cancel(self):
        for invoice in self.invoice_ids.filtered('auto_cancel_no_transaction'):
            invoice.action_invoice_cancel()
        return super()._set_transaction_cancel()

