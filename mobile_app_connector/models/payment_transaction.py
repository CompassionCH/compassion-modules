# coding: utf-8

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def cancel_mobile_transaction(self):
        for transaction in self:
            if transaction.invoice_id.origin in ["ios", "android"]:
                # Aborted transaction from the app. We must keep sponsorships but can
                # clean additional gifts
                inv = transaction.invoice_id
                inv.action_invoice_cancel()
                inv.invoice_line_ids = inv.invoice_line_ids.filtered(
                    lambda x: x.contract_id.id and x.product_id.id in
                    x.mapped('contract_id.contract_line_ids.product_id').ids
                )
                if inv.invoice_line_ids:
                    inv.action_invoice_draft()
                    inv.action_invoice_open()

    @api.multi
    def cancel_transaction(self):
        """
        Called by ir_action_rule in order to cancel the transaction that was
        not updated after a while.
        :return: True
        """
        self.cancel_mobile_transaction()
        return super(PaymentTransaction, self).cancel_transaction()

    @api.multi
    def cancel_transaction_on_update(self):
        """
        Called by ir_action_rule in order to cancel the transaction upon error
        :return: True
        """
        self.cancel_mobile_transaction()
        return super(PaymentTransaction, self).cancel_transaction_on_update()
