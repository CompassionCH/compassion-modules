##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields
from odoo.addons.queue_job.job import job, related_action


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @job(default_channel='root.cms_form_compassion')
    @related_action('related_action_invoice')
    def pay_transaction_invoice(
            self, transaction, invoice_vals, journal_id, method_id, auto_post):
        """Make a payment to reconcile transaction invoice.

        :param transaction: The originating transaction
        :param invoice_vals: Values to write into invoice
        :param journal_id: account.journal to use
        :param method_id: payment.method to use
        :param auto_post: True if invoice should be validated and payment
                          directly posted.
        :return: True
        """
        if self.state == 'paid':
            return True

        # Write values about payment
        self.write(invoice_vals)
        # Look for existing payment
        payment = self.env['account.payment'].search([
            ('invoice_ids', '=', self.id)
        ])
        if payment:
            return True

        payment_vals = {
            'journal_id': journal_id,
            'payment_method_id': method_id,
            'payment_date': fields.Date.today(),
            'communication': self.reference,
            'invoice_ids': [(6, 0, self.ids)],
            'payment_type': 'inbound',
            'amount': self.amount_total,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'customer',
            'payment_difference_handling': 'reconcile',
            'payment_difference': self.amount_total,
        }
        account_payment = self.env['account.payment'].create(payment_vals)
        if auto_post:
            # Validate self and post the payment.
            if self.state == 'draft':
                self.action_invoice_open()
            account_payment.post()
        self._after_transaction_invoice_paid(transaction)
        return True

    def _after_transaction_invoice_paid(self, transaction):
        """ Hook for doing post-processing after transaction was paid. """
        pass
