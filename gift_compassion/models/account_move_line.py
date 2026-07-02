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
            existing_gift_for_invl = self.env["sponsorship.gift"].search(
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
