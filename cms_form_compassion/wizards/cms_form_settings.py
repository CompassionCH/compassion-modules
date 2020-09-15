##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class CMSFormSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    match_validation_responsible = fields.Many2one(
        "res.users",
        string="Match partner validation responsible for activity schedule",
        domain=[("share", "=", False)],
        readonly=False,
    )

    @api.multi
    def set_values(self):
        super().set_values()
        # This is stored in page template for additional B2S pages
        config = self.env["ir.config_parameter"].sudo()
        config.set_param(
            "cms_form_compassion.match_validation_responsible", str(
                self.match_validation_responsible.id or 0)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()

        res["match_validation_responsible"] = int(
            config.get_param("cms_form_compassion.match_validation_responsible", 0)
        )
        return res
