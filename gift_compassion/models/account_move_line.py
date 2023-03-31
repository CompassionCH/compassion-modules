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
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

MSG_DONT_CANCEL_GIFT = "The invoice can't be unreconciled as the gift has already been sent to GMC or delivered."

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    gift_id = fields.Many2one("sponsorship.gift", "GMC Gift", readonly=False)

    def remove_move_reconcile(self):
        """
        Redefine the move to reconcile or not
        as we don't want certain gift invoice to be cancelled when the gift has already made his way to the child.
        """
        aml_to_unreconcile = self
        for aml in self:
            if aml.gift_id:
                gift_state = aml.gift_id.state
                # The gift can be delete if it wasn't send
                # but should avoid the unreconcile of the move line in case it was sent
                if gift_state in ['draft', 'verify']:
                    aml.gift_id.unlink()
                elif gift_state in ['In Progress', 'open', 'suspended', 'Delivered']:
                    if len(self) == 1:
                        raise UserError(MSG_DONT_CANCEL_GIFT)
                    else:
                        aml_to_unreconcile -= aml
                        _logger.warning(MSG_DONT_CANCEL_GIFT)

        return super(AccountMoveLine, aml_to_unreconcile).remove_move_reconcile()
