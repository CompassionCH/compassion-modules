# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

import itertools

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    """Generate automatically a BVR Reference for LSV Invoices"""
    _inherit = 'account.invoice'

    children = fields.Char(
        'Children', compute='_compute_children')
    last_payment = fields.Date(compute='_compute_last_payment', store=True)

    @api.depends('payment_move_line_ids', 'state')
    @api.multi
    def _compute_last_payment(self):
        for invoice in self.filtered('payment_move_line_ids'):
            filter = 'credit' if invoice.type == 'out_invoice' else 'debit'
            payment_dates = invoice.payment_move_line_ids.filtered(
                filter).mapped('date')
            invoice.last_payment = max(payment_dates or [False])

    @api.multi
    def _compute_children(self):
        """ View children contained in invoice. """
        for invoice in self:
            children = invoice.mapped('invoice_line_ids.contract_id.child_id')
            if len(children) > 1:
                invoice.children = _("{0} children".format(str(len(
                    children))))
            elif children:
                invoice.children = children.local_id
            else:
                invoice.children = False

    @api.multi
    def reconcile_after_clean(self):
        """
        Called after clean invoices. If invoices can be reconciled
        with open payment, this will split the payment into three amounts :
            - amount for reconciling the past invoices
            - amount for reconciling the future invoices
            - leftover amount that will stay in the client balance
        Then the invoices will be reconciled again
        :return: True
        """
        # At first we open again the cancelled invoices
        cancel_invoices = self.filtered(lambda i: i.state == 'cancel')
        cancel_invoices.action_invoice_draft()
        cancel_invoices.action_invoice_open()
        today = date.today()
        for partner_id in self.mapped('partner_id.id'):
            invoices = self.filtered(lambda i: i.partner_id.id == partner_id)
            past_invoices = invoices.filtered(
                lambda i: fields.Date.from_string(i.date_invoice) <= today)
            future_invoices = invoices - past_invoices
            past_amount = sum(past_invoices.mapped('amount_total'))
            future_amount = sum(future_invoices.mapped('amount_total'))
            is_past_reconciled = not past_invoices
            is_future_reconciled = not future_invoices

            # First try to find matching amount payments
            open_payments = self.env['account.move.line'].search([
                ('partner_id', '=', partner_id),
                ('account_id.code', '=', '1050'),
                ('reconciled', '=', False),
                ('credit', 'in', [past_amount, future_amount])
            ])
            for payment in open_payments:
                if not is_past_reconciled and payment.credit == past_amount:
                    past_invoices.mapped('')
                    is_past_reconciled = True
                elif not is_future_reconciled:
                    is_future_reconciled = True

            # If no matching payment found, we will group or split.
            if not is_past_reconciled:
                past_invoices._group_or_split_reconcile()
            if not is_future_reconciled:
                future_invoices._group_or_split_reconcile()

        return True

    @api.multi
    def _group_or_split_reconcile(self):
        """
        Find payments to reconcile given invoices and perform reconciliation.
        :return: True
        """
        partner = self.mapped('partner_id')
        partner.ensure_one()
        total_amount = sum(self.mapped('amount_total'))
        move_lines = self.mapped('move_id.line_ids').filtered('debit')
        payment_search = [
            ('partner_id', '=', partner.id),
            ('account_id.code', '=', '1050'),
            ('reconciled', '=', False),
            ('credit', '>', 0),
            ('credit', '>', total_amount)
        ]

        # First try to search a payment greater than the reconcile amount
        line_obj = self.env['account.move.line']
        open_payment = line_obj.search(
            payment_search, order='date asc', limit=1)
        if open_payment:
            # Split the payment move line to isolate reconcile amount
            (open_payment | move_lines).split_payment_and_reconcile()
        else:
            # Group several payments to match the invoiced amount
            # Limit to 12 move_lines to avoid too many computations
            open_payments = line_obj.search(payment_search[:-1], limit=12)
            # Search for a combination giving the invoiced amount
            # https://stackoverflow.com/questions/34517540/
            # find-all-combinations-of-a-list-of-numbers-with-a-given-sum
            credits = open_payments.mapped('credit')
            payment_ids = open_payments.ids
            matching_lines = line_obj
            must_split_move_line = False
            for i in range(2, len(credits)):
                for combination in itertools.combinations(credits, i):
                    if sum(combination) == total_amount:
                        matching_lines = line_obj.browse([
                            payment_ids[j] for j in combination])
                        break
                if matching_lines:
                    break
            else:
                # No combination found: we must split one payment
                payment_amount = 0
                nb_lines = 1
                for payment_line in open_payments:
                    missing_amount = total_amount - payment_amount
                    if payment_line.credit > missing_amount:
                        # Split last added line amount to perfectly match
                        # the total amount we are looking for
                        must_split_move_line = True
                        break

                    payment_amount += payment_line.credit
                    nb_lines += 1

                matching_lines = open_payments[:nb_lines]

            # Now reconcile matching lines with invoices
            if must_split_move_line:
                (matching_lines | move_lines).split_payment_and_reconcile()
            else:
                (matching_lines | move_lines).reconcile()

        return True
