##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_gift_refundable = fields.Boolean(compute="_compute_is_gift_refundable")

    def button_cancel(self):
        super().button_cancel()
        self.mapped("invoice_line_ids.gift_id").unlink()

    def _compute_is_gift_refundable(self):
        for move in self:
            if move.invoice_category in ["gift", "sponsorship"]:
                gifts = move.invoice_line_ids.mapped("gift_id")
                move.is_gift_refundable = not gifts or any(
                    gift.state in ["verify", "draft", "Undeliverable"] for gift in gifts
                )
            else:
                move.is_gift_refundable = True
