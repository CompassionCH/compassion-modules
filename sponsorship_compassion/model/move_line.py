# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class move_line(orm.Model):
    """ Adds a method to split a payment into several move_lines
    in order to reconcile only a partial amount, avoiding doing
    partial reconciliation. """
    _inherit = 'account.move.line'

    def split_payment_and_reconcile(self, cr, uid, ids, context=None):
        residual = 0.0
        count_credit_lines = 0
        move = False
        move_line = False

        for line in self.browse(cr, uid, ids, context):
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
        move_obj = self.pool.get('account.move')
        move_obj.button_cancel(cr, uid, [move.id], context)
        self.write(cr, uid, move_line.id, {
            'credit': move_line.credit-residual
        }, context)
        self.copy(cr, uid, move_line.id, default={
            'credit': residual,
            'name': context.get('residual_comment') or move_line.name
        }, context=context)
        move_obj.button_validate(cr, uid, [move.id], context)

        # Perform the reconciliation
        self.reconcile(cr, uid, ids)

        return True
