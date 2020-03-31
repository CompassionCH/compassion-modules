##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    invoice_id = fields.Many2one("account.invoice", "Invoice", readonly=False)

    @api.multi
    def cancel_transaction(self):
        """
        Called by ir_action_rule in order to cancel the transaction that
        was not updated after a while.
        :return: True
        """
        return self.write(
            {
                "state": "cancel",
                "state_message": "No update of the transaction within 10 minutes.",
            }
        )

    @api.multi
    def cancel_transaction_on_update(self):
        """
        Called by ir_action_rule in when transaction was cancelled by user.
        :return: True
        """
        return True

    @api.multi
    def confirm_transaction(self):
        """
        Called by ir_action_rule when transaction is done, to avoid missing
        payments in case the user quits the browser before he is redirected
        back to our website.
        :return: True
        """
        # Avoids launching several times the same job. Since there are 3
        # calls to the write method of payment.transaction during a transaction
        # feedback, this action_rule is triggered 3 times. We want to avoid it.
        for transaction in self:
            queue_job = self.env["queue.job"].search(
                [
                    ("channel", "=", "root.cms_form_compassion"),
                    ("state", "!=", "done"),
                    ("func_string", "like", str(transaction.id)),
                    ("name", "ilike", "reconcile transaction invoice"),
                ]
            )
            if not queue_job:
                invoice_vals = transaction._get_payment_invoice_vals()
                journal_id = transaction._get_payment_journal_id()
                method_id = transaction._get_payment_method_id()
                auto_post = transaction._get_auto_post_invoice()
                transaction.invoice_id.with_delay().pay_transaction_invoice(
                    transaction, invoice_vals, journal_id, method_id, auto_post
                )
        return True

    def render_sale_button(self, invoice, submit_txt=None, render_values=None):
        values = {
            "partner_id": self.partner_id.id,
            "billing_partner_id": self.partner_id.id,
        }
        if render_values:
            values.update(render_values)
        # Not very elegant to do that here but no choice regarding the design.
        self._log_payment_transaction_sent()
        return self.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=submit_txt or _('Pay Now')).sudo().render(
            self.reference,
            invoice.amount_total,
            invoice.company_id.currency_id.id,
            values=values,
        )

    def _get_payment_invoice_vals(self):
        # Can be overridden to add information from transaction into invoice.
        return {"payment_mode_id": self.payment_mode_id.id,
                "transaction_id": self.acquirer_reference
                }

    def _get_payment_journal_id(self):
        # Can be overridden
        return (
            self.env["account.journal"]
                .search(
                [
                    ("name", "=", "Web"),
                    ("company_id", "=", self.invoice_id.company_id.id),
                ]
            )
            .id
        )

    def _get_payment_method_id(self):
        # Can be overridden
        return (
            self.env["account.payment.method"]
                .search([("code", "=", "sepa_direct_debit")])
                .id
        )

    def _get_auto_post_invoice(self):
        # Can be overriden to determine if the payment can be posted
        return True
