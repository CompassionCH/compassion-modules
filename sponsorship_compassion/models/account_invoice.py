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
from odoo import api, fields, models, _


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
                invoice.children = _("{0} children".format(str(len(
                    children))))
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
        for invoice in self.filtered(lambda i: i.state in ('open', 'paid')):

            sponsorship_cat = self.env.ref(
                'sponsorship_compassion.product_category_sponsorship')
            fund_cat = self.env.ref(
                'contract_compassion.product_category_fund', -1)
            gift_cat = self.env.ref(
                'sponsorship_compassion.product_category_gift')

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
