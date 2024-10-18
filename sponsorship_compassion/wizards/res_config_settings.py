##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class StaffNotificationSettings(models.TransientModel):
    """Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    @api.model
    def write(self, values):
        if self.christmas_period_start_day and self.christmas_period_start_day == 31:
            if (
                self.christmas_period_start_month
                and self.christmas_period_start_month in (2, 4, 6, 9, 11)
            ):
                raise UserError("The selected month doesn't have 31 days !")
        if self.christmas_period_start_month and self.christmas_period_start_month == 2:
            if (
                self.christmas_period_start_day
                and self.christmas_period_start_day >= 29
            ):
                raise UserError(
                    "The Christmas period should work for all the years. "
                    "Some days such like February 29 don't exist every years and are "
                    "so blocked !"
                )
        result = super(StaffNotificationSettings, self).write(values)

    @api.model
    def _get_selection_months(self):
        months_number_select = []
        months_name_select = self.env["connect.month"].get_months_selection()[12:]
        months_number_select.append((0, ""))
        for i in range(12):
            months_number_select.append((i + 1, months_name_select[i][1]))
        return months_number_select

    @api.model
    def _get_selection_days_of_months(self):
        days_of_months_select = []
        for i in range(31):
            days_of_months_select.append((i + 1, i + 1))
        return days_of_months_select

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

    christmas_period_start_day = fields.Selection(
        selection=_get_selection_days_of_months,
        help="Choose the day from which the Christmas period begins. Postponed "
        "Christmas letters will be sent at this day and month.",
        config_parameter="sponsorship_compassion.christmas_period_start_day",
        default=20,
    )

    christmas_period_start_month = fields.Selection(
        selection=_get_selection_months,
        help="Choose the month from which the Christmas period begins. Postponed "
        "Christmas letters will be sent at this day and month.",
        config_parameter="sponsorship_compassion.christmas_period_start_month",
        default=12,
    )

    christmas_period_end_day = fields.Selection(
        selection=_get_selection_days_of_months,
        help="Choose the day from which the Christmas period ends. Christmas "
        "letters written after this day and month will be automatically "
        "postponed (To the next Christmas period).",
        config_parameter="sponsorship_compassion.christmas_period_end_day",
        default=30,
    )

    christmas_period_end_month = fields.Selection(
        selection=_get_selection_months,
        help="Choose the month from which the Christmas period ends. Christmas "
        "letters written after this day and month will be automatically "
        "postponed (To the next Christmas period).",
        config_parameter="sponsorship_compassion.christmas_period_end_month",
        default=12,
    )
