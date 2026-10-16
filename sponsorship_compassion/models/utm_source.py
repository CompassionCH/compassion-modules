##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models

# Medium of a sponsorship guessed from its source, when it has none: by source
# name, then by source category; "Other" when it cannot be guessed.
MEDIUM_BY_SOURCE = {
    "Radio": "Radio & TV",
    "TV": "Radio & TV",
    "BibelTV": "Radio & TV",
    "Korean TV programme": "Radio & TV",
    "Spanish TV and radio": "Radio & TV",
    "Google": "Online ads",
    "Social media": "Social media",
    "Facebook": "Social media",
    "facebook profile link french": "Social media",
    "facebook profile link italian": "Social media",
    "ig": "Social media",
    "Compassion newsletter": "Email",
    "Newsletter": "Email",
    "mailchimp": "Email",
}
MEDIUM_BY_CATEGORY = {
    "event": "Event",
    "fundraiser": "Website",
    "web": "Website",
    "ambassador": "Personal contact",
    "media": "Print",
    "advertising": "Print",
}


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

    def _guess_medium(self):
        """The medium of what this source brings, "Other" when unknown (empty
        when the media of the Compassion reports do not exist)."""
        name = MEDIUM_BY_SOURCE.get(self.name) or MEDIUM_BY_CATEGORY.get(
            self.category, "Other"
        )
        medium_obj = self.env["utm.medium"]
        return medium_obj.search([("name", "=", name)], limit=1) or medium_obj.search(
            [("name", "=", "Other")], limit=1
        )
