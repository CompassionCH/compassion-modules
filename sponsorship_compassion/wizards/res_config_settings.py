##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class StaffNotificationSettings(models.TransientModel):
    """Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    time_allowed_for_gifts = fields.Integer(
        help="Set number of days after sponsorship ending where gifts to the child "
        "are still allowed",
        config_parameter="sponsorship_compassion.time_allowed_for_gifts",
        default=90,
    )
    time_allowed_for_letters = fields.Integer(
        help="Set number of days after sponsorship ending where letters to the child "
        "are still allowed",
        config_parameter="sponsorship_compassion.time_allowed_for_letters",
        default=90,
    )

    christmas_inv_gen_month = fields.Integer(
        help="Chose the month at which the Christmas invoices will be generated. The "
        "due date will be one month after.",
        config_parameter="sponsorship_compassion.christmas_inv_gen_month",
        # Default invoices for Christmas gift are due for two months before Christmas
        default=9,
    )

    christmas_period_start_day = fields.Integer(
        help="Choose the day from which the Christmas period begins. Postponed "
        "Christmas letters will be sent at this day and month.",
        config_parameter="sponsorship_compassion.christmas_period_start_day",
        default=20,
    )

    christmas_period_start_month = fields.Integer(
        help="Choose the month from which the Christmas period begins. Postponed "
        "Christmas letters will be sent at this day and month.",
        config_parameter="sponsorship_compassion.christmas_period_start_month",
        default=12,
    )

    christmas_period_end_day = fields.Integer(
        help="Choose the day from which the Christmas period ends. Christmas "
        "letters written after this day and month will be automatically "
        "postponed (To the next Christmas period).",
        config_parameter="sponsorship_compassion.christmas_period_end_day",
        default=30,
    )

    christmas_period_end_month = fields.Integer(
        help="Choose the month from which the Christmas period ends. Christmas "
        "letters written after this day and month will be automatically "
        "postponed (To the next Christmas period).",
        config_parameter="sponsorship_compassion.christmas_period_end_month",
        default=12,
    )
