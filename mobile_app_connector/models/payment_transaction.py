import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def cancel_mobile_transaction(self):
        for transaction in self:
            if transaction.invoice_id.origin in ["ios", "android"]:
                # Aborted transaction from the app.
                transaction.invoice_id.action_invoice_cancel()

    def cancel_transaction(self):
        """
        Called by ir_action_rule in order to cancel the transaction that was
        not updated after a while.
        :return: True
        """
        self.cancel_mobile_transaction()
        return super(PaymentTransaction, self).cancel_transaction()

    def cancel_transaction_on_update(self):
        """
        Called by ir_action_rule in order to cancel the transaction upon error
        :return: True
        """
        self.cancel_mobile_transaction()
        return super(PaymentTransaction, self).cancel_transaction_on_update()

    def _get_payment_invoice_vals(self):
        # For mobile invoices, push the reference of transaction into invoice.
        vals = super(PaymentTransaction, self)._get_payment_invoice_vals()
        if self.invoice_id.origin in ["ios", "android"]:
            vals["name"] = self.reference
        return vals
