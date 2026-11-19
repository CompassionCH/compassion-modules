##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        res = super().button_draft()
        self.mapped("invoice_line_ids.gift_id").filtered(
            lambda g: not g.gmc_gift_id
        ).unlink()
        return res

    def _post(self, soft=True):
        """
        Make sure triggers for gifts
        are called after posting the move.
        """
        posted = super()._post(soft=soft)
        posted._filter_move_lines_to_gift()._trigger_gifts()
        return posted

    def write(self, vals):
        res = super().write(vals)
        if "line_ids" in vals:
            self._filter_move_lines_to_gift()._trigger_gifts()
        return res

    def _filter_move_lines_to_gift(self):
        return (
            self.filtered(
                lambda m: m.state == "posted"
                and (m.move_type == "entry" or m.payment_state == "paid")
            )
            .mapped("line_ids")
            .filtered(
                lambda line: line.product_id.categ_id
                == self.env.ref("sponsorship_compassion.product_category_gift")
                and line.contract_id.child_id
            )
        )
