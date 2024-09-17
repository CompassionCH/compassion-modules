##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class SBCSettings(models.TransientModel):
    """Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Users to notify after Child Departure
    letter_responsible = fields.Many2one(
        "res.users",
        string="Letter translation check unsuccessful",
        domain=[("share", "=", False)],
        readonly=False,
    )

    def set_values(self):
        super().set_values()
        # This is stored in page template for additional B2S pages
        config = self.env["ir.config_parameter"].sudo()
        config.set_param(
            "sbc_compassion.letter_responsible", str(self.letter_responsible.id or 0)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()
        user = self.env["res.users"]
        user_id = int(config.get_param("sbc_compassion.letter_responsible", 0))
        if user_id:
            user = user.browse(user_id)
        res["letter_responsible"] = user
        return res
