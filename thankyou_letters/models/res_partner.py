##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' namenoupdate="1"
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re
from datetime import datetime

from babel.dates import format_date

from odoo import fields, models


class ResPartner(models.Model):
    """Add fields for retrieving values for communications.

    - Short address
        Mr. John Doe
        Street
        City
        Country
    """

    _inherit = "res.partner"

    gender = fields.Selection(related="title.gender", readonly=True)
    thankyou_preference = fields.Selection(
        "_get_delivery_preference", default="auto_digital", required=True
    )
    short_address = fields.Char(compute="_compute_address")
    date_communication = fields.Char(compute="_compute_date_communication")

    def _compute_address(self):
        # Replace line returns
        p = re.compile("\\n+")
        for partner in self:
            res = ""
            t_partner = partner.with_context(lang=partner.lang)
            if not partner.is_company and partner.title.shortcut:
                res = t_partner.title.shortcut + " "
                if partner.firstname:
                    res += partner.firstname + " "
                res += (partner.lastname or "") + "<br/>"
            res += t_partner.contact_address
            partner.short_address = p.sub("<br/>", res)

    def _compute_date_communication(self):
        """City and date displayed in the top right of a letter"""
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for partner in self:
            date = format_date(today, format="long", locale=partner.lang)
            formatted_date = f"le {date}" if "fr" in partner.lang else date
            partner.date_communication = f"{city}, {formatted_date}"
