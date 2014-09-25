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

from openerp.osv import orm
from openerp.tools.translate import _
import logging

logger = logging.getLogger(__name__)


class reconcile_split_payment_wizard(orm.TransientModel):
    _name = 'reconcile.split.payment.wizard'

    def reconcile_split_payment(self, cr, uid, ids, context=None):
        ''' Generate an invoice corresponding to the selected fund
            and reconcile it with selected move lines
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

        if residual < 0:
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
