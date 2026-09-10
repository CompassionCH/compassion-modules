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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    gift_id = fields.Many2one(
        "sponsorship.gift", "GMC Gift", readonly=False, copy=False
    )

    def _trigger_gifts(self):
        gift_category = self.env.ref("sponsorship_compassion.product_category_gift")
        for move_line in self:
            existing_gift_for_invl = self.env["sponsorship.gift"].search_count(
                [("invoice_line_ids", "in", move_line.id)]
            )
            if (
                move_line.product_id.categ_id == gift_category
                and move_line.contract_id.child_id
                and not existing_gift_for_invl
            ):
                self.env["sponsorship.gift"].with_delay_sh(
                    "create_from_invoice_line",
                    move_line.id,
                    priority=50,
                    channel="root.gift_compassion",
                    identity_key=f"gift_from_inv_line_{move_line.id}",
                )

    def create(self, vals_list):
        res = super().create(vals_list)
        res.mapped("move_id")._filter_move_lines_to_gift()._trigger_gifts()
        return res

    def unlink(self):
        for gift in self.mapped("gift_id"):
            other_lines = gift.invoice_line_ids - self
            if not other_lines:
                if not gift.gmc_gift_id:
                    gift.unlink()
                else:
                    removed = sum(
                        line.price_subtotal
                        for line in self.filtered(
                            lambda _line, _gi=gift: _line.gift_id == _gi
                        )
                    )
                    gift.message_post(
                        body=f"{gift.currency_id.symbol} {removed} was removed "
                        f"from the invoice, but it is already sent to GMC."
                    )
        return super().unlink()
