##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class UtmSource(models.Model):
    _inherit = "utm.source"

    category = fields.Selection(
        [
            ("event", "Event"),
            ("fundraiser", "Fundraiser"),
            ("ambassador", "Ambassador"),
            ("existing_sponsor", "Existing sponsor"),
            ("media", "Media & publications"),
            ("advertising", "Advertising"),
            ("mailing", "Mailing"),
            ("web", "Website & social media"),
            ("transfer", "Transfer"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
        index=True,
        help="Kind of occasion that brought the sponsorship or donation, for the "
        "fundraising reports.",
    )
