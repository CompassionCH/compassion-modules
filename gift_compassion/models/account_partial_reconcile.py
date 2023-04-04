##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.exceptions import UserError

from odoo import models, _


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def unlink(self):
        """
        Remove pending gifts or prevent unreconcile if gift are already sent.
        """
        # This will retrieve all the lines of the reconciliation and the original move
        lines = (self.mapped('debit_move_id') + self.mapped('credit_move_id')).mapped('move_id.line_ids')
        for line in lines.filtered("gift_id"):
            gift = line.gift_id
            if gift.state in ['draft', 'verify']:
                gift.unlink()
            elif gift.state != 'Undeliverable':
                raise UserError(
                    _("You cannot delete the %s. It is already sent to GMC.")
                    % gift.name
                )
        super().unlink()
