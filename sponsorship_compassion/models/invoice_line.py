# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models, _


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    last_payment = fields.Date(
        related='invoice_id.last_payment', store=True)


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
