##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, _
from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_PRODUCTS_REF,
    PRODUCT_GIFT_CHRISTMAS
)


class RecurringContractGroup(models.Model):
    _inherit = "recurring.contract.group"

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def write(self, vals):
        res = super().write(vals)
        if vals.get("payment_mode_id", False):
            self._cancel_gift_inv()
        return res

    def _cancel_gift_inv(self):
        empty_move = self.env['account.move']
        contract_not_dd = self.mapped("contract_ids").filtered(lambda d: not d.is_direct_debit)
        for move_line in contract_not_dd.mapped("invoice_line_ids").filtered(
                lambda l: l.move_id.payment_state != 'paid' and l.move_id.state == 'posted'
                          and l.product_id.default_code in [PRODUCT_GIFT_CHRISTMAS, GIFT_PRODUCTS_REF[0]]
        ):
            move = move_line.move_id
            move.button_draft()
            group_id = move_line.contract_id.group_id
            if len(move.mapped("invoice_line_ids")) > 1:
                # We can move or remove the line
                move.write({"invoice_line_ids": [(2, move_line.id)]})
                message = "The invoice line has been removed "
            else:
                # The invoice would be empty if we remove the line
                message = "The invoice has been cancelled "
                empty_move |= move
            move.message_post(body=_(
                message + "because the payment mode of the <a href=# "
                          f"data-oe-model={self._name} data-oe-id={group_id.id}>"
                          f"Payment option ({group_id.ref})</a> has been modified")
            )
            group_id.message_post(body=_(
                "Because of the payment method modification on this payment option. "
                f"The <a href=# data-oe-model={move._name} data-oe-id={move.id}>invoice ({move.name})</a>"
                " has been cancelled." if "cancelled" in message else " has some line that were unlink."

            ))
        empty_move.button_cancel()
