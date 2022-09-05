##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class AvailabilitySettings(models.TransientModel):
    """ Settings configuration for Demand Planning."""

    _inherit = "res.config.settings"

    # Hold default durations
    consignment_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.consignment_hold_duration", default=14)
    e_commerce_hold_duration = fields.Integer(
        help="In Minutes", config_parameter="child_compassion.e_commerce_hold_duration", default=15)
    no_money_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.no_money_hold_duration", default=30)
    no_money_hold_extension = fields.Integer(
        help="In Days", config_parameter="child_compassion.no_money_hold_extension", default=15)
    reinstatement_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.reinstatement_hold_duration", default=15)
    reservation_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.reservation_duration", default=30)
    reservation_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.reservation_hold_duration", default=7)
    sponsor_cancel_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.sponsor_cancel_hold_duration", default=7)
    sub_child_hold_duration = fields.Integer(
        help="In Days", config_parameter="child_compassion.sub_child_hold_duration", default=30)
