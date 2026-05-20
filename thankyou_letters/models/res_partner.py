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
from markupsafe import Markup, escape

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
        p = re.compile(r"\n+")
        for partner in self:
            t_partner = partner.with_context(lang=partner.lang)
            lines = []
            if not partner.is_company and partner.title.shortcut:
                title = escape(t_partner.title.shortcut)
                firstname = escape(partner.firstname or "")
                lastname = escape(partner.lastname or "")
                full_name = " ".join(
                    part for part in [title, firstname, lastname] if part
                )
                lines.append(full_name)
            lines.append(escape(t_partner.contact_address or ""))
            text = "\n".join(str(line) for line in lines if line)
            partner.short_address = Markup(p.sub("<br/>", text))

    def _compute_date_communication(self):
        """City and date displayed in the top right of a letter"""
        today = datetime.today()
        city = self.env.user.partner_id.company_id.city
        for partner in self:
            date = format_date(today, format="long", locale=partner.lang)
            formatted_date = f"le {date}" if "fr" in partner.lang else date
            partner.date_communication = f"{city}, {formatted_date}"
