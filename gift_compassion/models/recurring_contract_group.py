##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, models

from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_PRODUCTS_REF,
    PRODUCT_GIFT_CHRISTMAS,
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
        empty_move = self.env["account.move"]
        contract_not_dd = self.mapped("contract_ids").filtered(
            lambda d: not d.is_direct_debit
        )
        for move_line in contract_not_dd.mapped("invoice_line_ids").filtered(
            lambda line: line.move_id.payment_state != "paid"
            and line.move_id.state == "posted"
            and line.product_id.default_code
            in [PRODUCT_GIFT_CHRISTMAS, GIFT_PRODUCTS_REF[0]]
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
            # dynamic parts of the message are inserted after the translation marker _(), which prevent name 'self' is not defined error during term extraction.
            message_template = "{} because the payment mode of the <a href=# data-oe-model={} data-oe-id={}>Payment option ({})</a> has been modified"
            formatted_message = message_template.format(message, self._name, group_id.id, group_id.ref)
            move.message_post(body=_(formatted_message))

            # Determine the conditional part of the message first
            conditional_message = (
                "Because of the payment method modification on this payment option. "
                "The <a href=# data-oe-model={} data-oe-id={}>invoice ({})</a> has been cancelled."
                if "cancelled" in message else
                " has some lines that were unlinked."
            )
            # Now format the dynamic content into the message
            if "cancelled" in message:
                formatted_message = conditional_message.format(move._name, move.id, move.name)
            else:
                formatted_message = conditional_message
            # Finally, post the message
            group_id.message_post(body=_(formatted_message))

        empty_move.button_cancel()
