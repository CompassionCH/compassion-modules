##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    time_allowed_for_gifts = fields.Integer(
        help="Set number of days after sponsorship ending where gifts to the child "
             "are still allowed"
    )
    time_allowed_for_letters = fields.Integer(
        help="Set number of days after sponsorship ending where letters to the child "
             "are still allowed"
    )

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "sponsorship_compassion.time_allowed_for_gifts",
            str(
                self.time_allowed_for_gifts
                if self.time_allowed_for_gifts
                else 90
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "sponsorship_compassion.time_allowed_for_letters",
            str(
                self.time_allowed_for_letters
                if self.time_allowed_for_letters
                else 90
            ),
        )

    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "time_allowed_for_gifts": int(
                    param_obj.get_param(
                        "sponsorship_compassion.time_allowed_for_gifts", None
                    )
                    or 90
                )
                or 90,
                "time_allowed_for_letters": int(
                    param_obj.get_param(
                        "sponsorship_compassion.time_allowed_for_letters", None
                    )
                    or 90
                )
                or 90,
            }
        )
        return res
