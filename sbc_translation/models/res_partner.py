##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    translation_user_id = fields.Many2one(
        "translation.user",
        string="Translation User",
        help="Allow to engage the partner in translations.",
        compute="_compute_translator",
        readonly=False,
        store=True,
    )

    def _compute_translator(self):
        for partner in self:
            partner.translation_user_id = self.env["translation.user"].search(
                [("partner_id", "=", partner.id)], limit=1
            )
