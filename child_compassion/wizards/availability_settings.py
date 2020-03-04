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


class AvailabilitySettings(models.TransientModel):
    """ Settings configuration for Demand Planning."""

    _inherit = "res.config.settings"

    # Hold default durations
    consignment_hold_duration = fields.Integer(help="In Days")
    e_commerce_hold_duration = fields.Integer(help="In Minutes")
    no_money_hold_duration = fields.Integer(help="In Days")
    no_money_hold_extension = fields.Integer(help="In Days")
    reinstatement_hold_duration = fields.Integer(help="In Days")
    reservation_duration = fields.Integer(help="In Days")
    reservation_hold_duration = fields.Integer(help="In Days")
    sponsor_cancel_hold_duration = fields.Integer(help="In Days")
    sub_child_hold_duration = fields.Integer(help="In Days")

    @api.multi
    def set_values(self):
        super().set_values()
        config = self.env["ir.config_parameter"]
        config.set_param(
            "child_compassion.consignment_hold_duration",
            str(self.consignment_hold_duration),
        )
        config.set_param(
            "child_compassion.e_commerce_hold_duration",
            str(self.e_commerce_hold_duration),
        )
        config.set_param(
            "child_compassion.no_money_hold_duration", str(self.no_money_hold_duration)
        )
        config.set_param(
            "child_compassion.no_money_hold_extension",
            str(self.no_money_hold_extension),
        )
        config.set_param(
            "child_compassion.reinstatement_hold_duration",
            str(self.reinstatement_hold_duration),
        )
        config.set_param(
            "child_compassion.reservation_duration", str(self.reservation_duration)
        )
        config.set_param(
            "child_compassion.reservation_hold_duration",
            str(self.reservation_hold_duration),
        )
        config.set_param(
            "child_compassion.sponsor_cancel_hold_duration",
            str(self.sponsor_cancel_hold_duration),
        )
        config.set_param(
            "child_compassion.sub_child_hold_duration",
            str(self.sub_child_hold_duration),
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"]

        res["consignment_hold_duration"] = int(
            param_obj.get_param("child_compassion.consignment_hold_duration", "14")
        )
        res["e_commerce_hold_duration"] = int(
            param_obj.get_param("child_compassion.e_commerce_hold_duration", "15")
        )
        res["no_money_hold_duration"] = int(
            param_obj.get_param("child_compassion.no_money_hold_duration", "30")
        )
        res["no_money_hold_extension"] = int(
            param_obj.get_param("child_compassion.no_money_hold_extension", "15")
        )
        res["reinstatement_hold_duration"] = int(
            param_obj.get_param("child_compassion.reinstatement_hold_duration", "15")
        )
        res["reservation_duration"] = int(
            param_obj.get_param("child_compassion.reservation_duration", "30")
        )
        res["reservation_hold_duration"] = int(
            param_obj.get_param("child_compassion.reservation_hold_duration", "7")
        )
        res["sponsor_cancel_hold_duration"] = int(
            param_obj.get_param("child_compassion.sponsor_cancel_hold_duration", "7")
        )
        res["sub_child_hold_duration"] = int(
            param_obj.get_param("child_compassion.sub_child_hold_duration", "30")
        )

        return res

    @api.model
    def get_param(self, param):
        """Get a single param from ['res.config.settings']"""
        return self.sudo().get_values()[param]
