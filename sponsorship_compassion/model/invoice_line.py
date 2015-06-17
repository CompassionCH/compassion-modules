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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import mod10r

from .product import GIFT_CATEGORY, SPONSORSHIP_CATEGORY


class invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    def _get_last_payment(self, cr, uid, ids, name, dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            last_date = None
            for payment in line.invoice_id.payment_ids:
                if payment.credit > 0 and payment.date > last_date:
                    last_date = payment.date
            res[line.id] = last_date

        return res

    def _get_invoice_lines(self, cr, uid, ids, context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(cr, uid,
                                           [('invoice_id', 'in', ids)],
                                           context=context)
        return inv_line_ids

    _columns = {
        'last_payment': fields.function(
            _get_last_payment, string=_('Last Payment'), type='date',
            store={'account.invoice': (_get_invoice_lines,
                                       ['payment_ids', 'state'], 20)}),
    }


class account_invoice(orm.Model):
    """Generate automatically a BVR Reference for LSV Invoices"""
    _inherit = 'account.invoice'

    def _get_children(self, cr, uid, ids, name, args, context=None):
        """ View children contained in invoice. """
        res = dict()
        for invoice in self.browse(cr, uid, ids, context):
            child_codes = set()
            for invl in invoice.invoice_line:
                child = invl.contract_id and invl.contract_id.child_id
                if child:
                    child_codes.add(child.code)
            if len(child_codes) > 1:
                res[invoice.id] = _("{0} children".format(str(len(
                    child_codes))))
            elif child_codes:
                res[invoice.id] = child_codes.pop()
            else:
                res[invoice.id] = False
        return res

    _columns = {
        'children': fields.function(
            _get_children, type='char', string=_('Children'))
    }

    def action_date_assign(self, cr, uid, ids, context=None):
        """Method called when invoice is validated.
            - Add BVR Reference if payment term is LSV and no reference is
              set.
            - Prevent validating invoices missing related contract.
        """
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.payment_term and 'LSV' in invoice.payment_term.name \
                    and not invoice.bvr_reference:
                seq = self.pool.get('ir.sequence')
                ref = mod10r(seq.next_by_code(cr, uid, 'contract.bvr.ref'))
                invoice.write({'bvr_reference': ref})
            for invl in invoice.invoice_line:
                if not invl.contract_id and invl.product_id.categ_name in (
                        SPONSORSHIP_CATEGORY, GIFT_CATEGORY):
                    raise orm.except_orm(
                        _('Sponsorship missing in invoice'),
                        _("Invoice %s for '%s' is missing a sponsorship.") %
                        (str(invoice.id), invoice.partner_id.name))

        return super(account_invoice, self).action_date_assign(cr, uid, ids,
                                                               context)
