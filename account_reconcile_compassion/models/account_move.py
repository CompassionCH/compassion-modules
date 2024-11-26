##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.move"

    bank_statement_id = fields.Many2one("account.bank.statement", "Bank statement")
    to_reconcile = fields.Float()

    def change_attribution(self):
        self.ensure_one()
        move_line_obj = self.env["account.move.line"]
        if self.amount_total != self.to_reconcile:
            raise UserError(
                _(
                    "The invoice total amount should be equal to %s in order to"
                    " be reconciled against the payment."
                )
                % self.to_reconcile
            )

        self.action_invoice_open()

        # Reconcile all related move lines
        mvl_ids = self.env.context.get("payment_ids")
        if mvl_ids:
            move_lines = move_line_obj.search(
                [
                    ("move_id", "=", self.move_id.id),
                    ("account_id", "=", self.account_id.id),
                ]
            )
            move_lines |= move_line_obj.browse(mvl_ids)
            move_lines.reconcile("manual")
        self.to_reconcile = 0.0
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)

    def reconcile(self):
        # OVERRIDE
        # List in_payment invoices

        all_lines = self + self.matched_debit_ids.debit_move_id + self.matched_credit_ids.credit_move_id
        payments = all_lines.move_id.filtered(lambda move: move.payment_id or move.statement_line_id)

        invoices = payments._get_reconciled_invoices()

        in_payment_invoices = invoices.filtered(
            lambda move: move.is_invoice(include_receipts=True) and move.payment_state in ('in_payment')
        )

        res = super().reconcile()

        # Trigger action for paid invoices
        in_payment_invoices \
            .filtered(lambda move: move.payment_state in ('paid')) \
            .action_invoice_paid()
        return res
