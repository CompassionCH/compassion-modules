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


class account_invoice(orm.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    _columns = {
        'recurring_invoicer_id': fields.many2one(
            'recurring.invoicer', _('Invoicer')),
    }


class account_invoice_line(orm.Model):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    def _get_dates(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = line.invoice_id.date_due or False

        return res

    def _get_states(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = line.invoice_id.state

        return res

    def _get_invoice_lines(self, cr, uid, ids, context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(cr, uid,
                                           [('invoice_id', 'in', ids)],
                                           context=context)
        return inv_line_ids

    _columns = {
        'contract_id': fields.many2one(
            'recurring.contract', _('Source contract')),
        'due_date': fields.function(
            _get_dates, string=_('Due date'), readonly=True, type='date',
            store={'account.invoice': (_get_invoice_lines, ['date_due'], 20)}),
        'state': fields.function(
            _get_states, string=_('State'), readonly=True, type='selection',
            selection=[('draft', 'Draft'),
                       ('proforma', 'Pro-forma'),
                       ('proforma2', 'Pro-forma'),
                       ('open', 'Open'),
                       ('paid', 'Paid'),
                       ('cancel', 'Cancelled')],
            store={'account.invoice': (_get_invoice_lines, ['state'], 20)}),
    }
