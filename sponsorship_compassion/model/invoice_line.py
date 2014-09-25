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

    def _get_child_ref(self, cr, uid, ids, name, dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if line.contract_id and line.contract_id.child_id:
                child = line.contract_id.child_id
                res[line.id] = child.code + ' ' + child.name

        return res

    def _get_invoice_lines(self, cr, uid, ids, context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(cr, uid,
                                           [('invoice_id', 'in', ids)],
                                           context=context)
        return inv_line_ids

    def _get_inv_line_from_contract(self, cr, uid, ids, context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(cr, uid,
                                           [('contract_id', 'in', ids)],
                                           context=context)
        return inv_line_ids

    _columns = {
        'child_name': fields.function(
            _get_child_ref, string=_('Sponsored child'), readonly=True,
            type='char',
            store={'account.invoice.line': (lambda self, cr, uid, ids, c={}:
                                            ids, ['contract_id'], 50),
                   'reccuring.contract': (_get_inv_line_from_contract,
                                          ['child_id'], 20)}),
        'last_payment': fields.function(
            _get_last_payment, string=_('Last Payment'), type='date',
            store={'account.invoice': (_get_invoice_lines,
                                       ['payment_ids', 'state'], 20)}),
    }
