# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, exceptions, fields, models, _
from openerp.tools import mod10r

from .product import GIFT_CATEGORY, SPONSORSHIP_CATEGORY


class invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    last_payment = fields.Date(
        compute='_set_last_payment', store=True)

    @api.multi
    @api.depends('invoice_id.payment_ids', 'state')
    def _set_last_payment(self):
        for line in self:
            last_date = None
            for payment in line.invoice_id.payment_ids:
                if payment.credit > 0 and payment.date > last_date:
                    last_date = payment.date
            line.last_payment = last_date


class account_invoice(models.Model):
    """Generate automatically a BVR Reference for LSV Invoices"""
    _inherit = 'account.invoice'

    children = fields.Char(
        'Children', compute='_set_children')

    @api.multi
    def _set_children(self):
        """ View children contained in invoice. """
        for invoice in self:
            children = invoice.mapped('invoice_line.contract_id.child_id')
            if len(children) > 1:
                invoice.children = _("{0} children".format(str(len(
                    children))))
            elif children:
                invoice.children = children.code
            else:
                invoice.children = False

    @api.multi
    def action_date_assign(self):
        """Method called when invoice is validated.
            - Add BVR Reference if payment term is LSV and no reference is
              set.
            - Prevent validating invoices missing related contract.
        """
        for invoice in self:
            if invoice.payment_term and 'LSV' in invoice.payment_term.name \
                    and not invoice.bvr_reference:
                seq = self.env['ir.sequence']
                ref = mod10r(seq.next_by_code('contract.bvr.ref'))
                invoice.write({'bvr_reference': ref})
            for invl in invoice.invoice_line:
                if not invl.contract_id and invl.product_id.categ_name in (
                        SPONSORSHIP_CATEGORY, GIFT_CATEGORY):
                    raise exceptions.Warning(
                        _('Sponsorship missing in invoice'),
                        _("Invoice %s for '%s' is missing a sponsorship.") %
                        (str(invoice.id), invoice.partner_id.name))

        return super(account_invoice, self).action_date_assign()
