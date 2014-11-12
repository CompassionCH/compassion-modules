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


class reconcile_split_payment_wizard(orm.TransientModel):
    """Wizard that helps the user doing a full reconciliation when a customer
    paid more than excepted. It splits the payment into two move lines so
    that one invoice can be reconciled and the extra amount is kept in
    the customer balance. """
    _name = 'reconcile.split.payment.wizard'

    def _get_default_ids(self, cr, uid, context=None):
        return self._get_contract_ids(cr, uid, [0], 'contract_id', '',
                                      context)[0]

    def _get_contract_ids(self, cr, uid, ids, field_name, arg, context):
        move_line_obj = self.pool.get('account.move.line')
        contract_ids = set()
        active_ids = context.get('active_ids')
        if active_ids:
            for move_line in move_line_obj.browse(cr, uid, active_ids,
                                                  context):
                if move_line and move_line.debit > 0:
                    invoice = move_line.invoice
                    if invoice and invoice.amount_total == move_line.debit:
                            contract_ids.update([invoice_line.contract_id.id
                                                 for invoice_line in
                                                 invoice.invoice_line])
        return {id: list(contract_ids) for id in ids}

    def _write_contracts(self, cr, uid, ids, field_name, field_value, arg,
                         context):
        value_obj = self.pool.get('recurring.contract')
        for line in field_value:
            if line[0] == 1:  # one2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True

    _columns = {
        'contract_ids': fields.function(
            _get_contract_ids, fnct_inv=_write_contracts, type='one2many',
            obj='recurring.contract', method=True,
            string=_('Related contracts'),
            help=_('You can directly edit the contracts from here if you want '
                   'to change the next invoice date of one contract '
                   'so that they are not charged in a same invoice.')),
    }

    _defaults = {
        'contract_ids': _get_default_ids,
    }

    def reconcile_split_payment(self, cr, uid, ids, context=None):
        ''' Split the payment of a partner into two move_lines in order to
        reconcile one of them.
        '''
        move_line_obj = self.pool.get('account.move.line')
        active_ids = context.get('active_ids')

        return move_line_obj.split_payment_and_reconcile(cr, uid, active_ids,
                                                         context)
