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
import logging

logger = logging.getLogger(__name__)


class reconcile_split_payment_wizard(orm.TransientModel):
    _name = 'reconcile.split.payment.wizard'

    def _get_default_ids(self, cr, uid, context=None):
        return self._get_contract_ids(cr, uid, [0], 'contract_id', '',
                                      context)[0]

    def _get_contract_ids(self, cr, uid, ids, field_name, arg, context):
        move_line_obj = self.pool.get('account.move.line')
        contract_ids = []
        active_ids = context.get('active_ids')
        if active_ids:
            for move_line in move_line_obj.browse(cr, uid, active_ids,
                                                  context):
                if move_line and move_line.debit > 0:
                    invoice = move_line.invoice
                    if invoice:
                        for invoice_line in invoice.invoice_line:
                            if invoice_line.price_subtotal == move_line.debit:
                                contract_ids.append(
                                    invoice_line.contract_id.id)

        return dict([(id, contract_ids) for id in ids])

    def _write_contracts(self, cr, uid, ids, field_name, field_value, arg,
                         context):
        value_obj = self.pool.get('simple.recurring.contract')
        for line in field_value:
            if line[0] == 1:  # one2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True

    _columns = {
        'contract_ids': fields.function(
            _get_contract_ids, fnct_inv=_write_contracts, type='one2many',
            obj='simple.recurring.contract', method=True,
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
        if isinstance(ids, list):
            ids = ids[0]

        # wizard = self.browse(cr, uid, ids, context)
        move_line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        active_ids = context.get('active_ids')

        residual = 0.0
        count_credit_lines = 0
        move = False
        move_line = False

        for line in move_line_obj.browse(cr, uid, active_ids,
                                         context):
            residual += line.credit - line.debit
            if line.credit > 0:
                move = line.move_id
                move_line = line
                count_credit_lines += 1

        if residual <= 0:
            raise orm.except_orm(
                'ResidualError',
                _('This can only be done if credits > debits'))

        if count_credit_lines != 1:
            raise orm.except_orm(
                'CreditLineError',
                _('This can only be done for one credit line'))

        # Edit move in order to split payment into two move lines
        move_obj.button_cancel(cr, uid, [move.id], context)
        move_line_obj.write(cr, uid, move_line.id, {
            'credit': move_line.credit-residual
        }, context)
        move_line_obj.copy(cr, uid, move_line.id, default={
            'credit': residual
        }, context=context)
        move_obj.button_validate(cr, uid, [move.id], context)

        # Perform the reconciliation
        move_line_obj.reconcile(cr, uid, active_ids)

        return True
