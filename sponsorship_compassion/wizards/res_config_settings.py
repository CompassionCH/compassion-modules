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
             "are still allowed",
        config_parameter="sponsorship_compassion.time_allowed_for_gifts",
        default=90
    )
    time_allowed_for_letters = fields.Integer(
        help="Set number of days after sponsorship ending where letters to the child "
             "are still allowed",
        config_parameter="sponsorship_compassion.time_allowed_for_letters",
        default=90
    )

    christmas_inv_due_date = fields.Char(
        help="Set date for the generation of the christmas gift invoices "
             "This date will automatically be set two month in the past "
             "are still allowed",
        config_parameter="sponsorship_compassion.christmas_inv_due_date",
        # Default invoices for christmas gift are due for two months beofre christmas
        default=fields.Date.to_string(fields.date.today().replace(month=10, day=25))
    )
