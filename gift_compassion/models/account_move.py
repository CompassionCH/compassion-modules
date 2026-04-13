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
