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

from openerp import api, exceptions, models, _


class move_line(models.Model):
    """ Adds a method to split a payment into several move_lines
    in order to reconcile only a partial amount, avoiding doing
    partial reconciliation. """
    _inherit = 'account.move.line'

    @api.multi
    def split_payment_and_reconcile(self):
        residual = 0.0
        count_credit_lines = 0
        move = False
        move_line = False

        for line in self:
            residual += line.credit - line.debit
            if line.credit > 0:
                move = line.move_id
                move_line = line
                count_credit_lines += 1

        if residual <= 0:
            raise exceptions.Warning(
                _('This can only be done if credits > debits'))

        if count_credit_lines != 1:
            raise exceptions.Warning(
                _('This can only be done for one credit line'))

        # Edit move in order to split payment into two move lines
        move.button_cancel()
        move_line.write({
            'credit': move_line.credit-residual
        })
        move_line.copy(default={
            'credit': residual,
            'name': self.env.context.get('residual_comment') or move_line.name
        })
        move.button_validate()

        # Perform the reconciliation
        self.reconcile()

        return True
