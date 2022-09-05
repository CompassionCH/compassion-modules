##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class SdsFollowerSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Users to notify after Child Departure
    sub_fr = fields.Many2one(
        "res.users",
        string="Sub sponsorships (FR)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    sub_de = fields.Many2one(
        "res.users",
        string="Sub sponsorships (DE)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    sub_it = fields.Many2one(
        "res.users",
        string="Sub sponsorships (IT)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    sub_en = fields.Many2one(
        "res.users",
        string="Sub sponsorships (EN)",
        domain=[("share", "=", False)],
        readonly=False,
    )

    def set_values(self):
        super().set_values()
        config = self.env["ir.config_parameter"].sudo()
        config.set_param(
            "sponsorship_tracking.sub_follower_fr", str(self.sub_fr.id or 0)
        )
        config.set_param(
            "sponsorship_tracking.sub_follower_de", str(self.sub_de.id or 0)
        )
        config.set_param(
            "sponsorship_tracking.sub_follower_it", str(self.sub_it.id or 0)
        )
        config.set_param(
            "sponsorship_tracking.sub_follower_en", str(self.sub_en.id or 0)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()

        res["sub_fr"] = int(
            config.get_param("sponsorship_tracking.sub_follower_fr", self.env.uid)
        )
        res["sub_de"] = int(
            config.get_param("sponsorship_tracking.sub_follower_de", self.env.uid)
        )
        res["sub_it"] = int(
            config.get_param("sponsorship_tracking.sub_follower_it", self.env.uid)
        )
        res["sub_en"] = int(
            config.get_param("sponsorship_tracking.sub_follower_en", self.env.uid)
        )
        return res
