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
from odoo import api, fields, models, _
from datetime import date

class AccountInvoice(models.Model):
    """Generate automatically a BVR Reference for LSV Invoices"""
    _inherit = 'account.invoice'

    children = fields.Char(
        'Children', compute='_compute_children')
    last_payment = fields.Date(compute='_compute_last_payment', store=True)
    invoice_type = fields.Selection([
        ('sponsorship', 'Sponsorship'),
        ('gift', 'Gift'),
        ('fund', 'Fund donation'),
        ('other', 'Other'),
    ], compute='_compute_invoice_type', store=True)

    @api.multi
    def _compute_children(self):
        """ View children contained in invoice. """
        for invoice in self:
            children = invoice.mapped('invoice_line_ids.contract_id.child_id')
            if len(children) > 1:
                num_children = len(children)
                invoice.children = f"{num_children} children"
            elif children:
                invoice.children = children.local_id
            else:
                invoice.children = False

    @api.depends('payment_move_line_ids', 'state')
    @api.multi
    def _compute_last_payment(self):
        for invoice in self.filtered('payment_move_line_ids'):
            mv_filter = 'credit' if invoice.type == 'out_invoice' else 'debit'
            payment_dates = invoice.payment_move_line_ids.filtered(
                mv_filter).mapped('date')
            invoice.last_payment = max(payment_dates or [False])

    @api.depends('invoice_line_ids', 'state')
    @api.multi
    def _compute_invoice_type(self):
        sponsorship_cat = self.env.ref(
            'sponsorship_compassion.product_category_sponsorship', False)
        fund_cat = self.env.ref(
            'sponsorship_compassion.product_category_fund', False)
        gift_cat = self.env.ref(
            'sponsorship_compassion.product_category_gift', False)
        # At module installation, the categories are not yet loaded.
        if not sponsorship_cat or not fund_cat or not gift_cat:
            return
        for invoice in self.filtered(lambda i: i.state in ('open', 'paid')):
            # check if child_of Sponsorship category
            category_lines = self.env['account.invoice.line'].search([
                ('invoice_id', '=', invoice.id),
                ('product_id.categ_id', 'child_of', sponsorship_cat.id)
            ])

            if category_lines:
                invoice.invoice_type = 'sponsorship'
            else:
                # check if child_of Gift category
                category_lines = self.env['account.invoice.line'].search([
                    ('invoice_id', '=', invoice.id),
                    ('product_id.categ_id', 'child_of', gift_cat.id)
                ])
                if category_lines:
                    invoice.invoice_type = 'gift'
                else:
                    # check if child_of Fund category
                    category_lines = self.env['account.invoice.line'].search([
                        ('invoice_id', '=', invoice.id),
                        ('product_id.categ_id', 'child_of', fund_cat.id)
                    ])
                    if category_lines:
                        invoice.invoice_type = 'fund'
                    else:
                        # last choice -> Other category
                        invoice.invoice_type = 'other'

    @api.multi
    def action_invoice_paid(self):
        """ Call invoice_paid method on related contracts. """
        res = super(AccountInvoice, self).action_invoice_paid()
        for invoice in self:
            contracts = invoice.mapped('invoice_line_ids.contract_id')
            contracts.invoice_paid(invoice)
        return res

    @api.multi
    def action_invoice_re_open(self):
        """ Call invoice_unpaid method on related contract. """
        res = super(AccountInvoice, self).action_invoice_re_open()
        for invoice in self:
            contracts = invoice.mapped('invoice_line_ids.contract_id')
            contracts.invoice_unpaid(invoice)
        return res

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
        reconcile_amount = sum(self.mapped('amount_total'))
        move_lines = self.mapped('move_id.line_ids').filtered('debit')
        payment_search = [
            ('partner_id', '=', partner.id),
            ('account_id.code', '=', '1050'),
            ('reconciled', '=', False),
            ('credit', '>', 0)
        ]

        line_obj = self.env['account.move.line']
        payment_greater_than_reconcile = line_obj.search(
            payment_search + [('credit', '>', reconcile_amount)],
            order='date asc', limit=1)
        if payment_greater_than_reconcile:
            # Split the payment move line to isolate reconcile amount
            (payment_greater_than_reconcile | move_lines) \
                .split_payment_and_reconcile()
            return True
        else:
            # Group several payments to match the invoiced amount
            # Limit to 12 move_lines to avoid too many computations
            open_payments = line_obj.search(payment_search, limit=12)

            # Search for a combination giving the invoiced amount recursively
            # https://stackoverflow.com/questions/4632322/finding-all-possible-
            # combinations-of-numbers-to-reach-a-given-sum
            def find_sum(numbers, target, partial=None):
                if partial is None:
                    partial = []
                s = sum(p.credit for p in partial)

                if s == target:
                    return partial
                if s >= target:
                    return  # if we reach the number why bother to continue

                for i in range(len(numbers)):
                    ret = find_sum(numbers[i + 1:], target,
                                   partial + [numbers[i]])
                    if ret is not None:
                        return ret

            matching_lines = line_obj
            sum_found = find_sum(open_payments, reconcile_amount)
            if sum_found is not None:
                for payment in sum_found:
                    matching_lines += payment
                return (matching_lines | move_lines).reconcile()
            else:
                # No combination found: we must split one payment
                payment_amount = 0
                for index, payment_line in enumerate(open_payments):
                    missing_amount = reconcile_amount - payment_amount
                    if payment_line.credit > missing_amount:
                        # Split last added line amount to perfectly match
                        # the total amount we are looking for
                        return (open_payments[:index + 1] | move_lines) \
                            .split_payment_and_reconcile()
                    payment_amount += payment_line.credit
                return (open_payments | move_lines).reconcile()
