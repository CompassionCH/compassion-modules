import re

from odoo import fields, models
from odoo.tools.mail import html2plaintext


class MailingTrace(models.Model):
    _inherit = ["mailing.trace", "interaction.source"]
    _name = "mailing.trace"

    _STATUS_MAPPING = {
        "open": "opened",
        "reply": "replied",
        "bounce": "bounced",
        "error": "exception",
        "cancel": "canceled",
    }

    date = fields.Datetime(related="sent_datetime", search="_search_date")

    def _search_date(self, operator, value):
        return [("sent_datetime", operator, value)]

    def _get_body(self):
        self.ensure_one()
        res = ""
        if self.mass_mailing_id.body_html:
            re_pattern = re.compile(r"(\n)+")
            res = html2plaintext(self.mass_mailing_id.body_html)
            res = re_pattern.sub("\n", res)
        return res

    def _get_interaction_data(self, partner_id):
        return [
            {
                "partner_id": partner_id,
                "res_model": self._name,
                "res_id": rec.id,
                "direction": "out",
                "date": rec.sent_datetime,
                "email": rec.email,
                "communication_type": "Mass",
                "subject": rec.mass_mailing_id.subject,
                "body": rec._get_body(),
                "has_attachment": bool(rec.mass_mailing_id.attachment_ids),
                "tracking_status": self._STATUS_MAPPING.get(
                    rec.trace_status, rec.trace_status
                ),
            }
            for rec in self
        ]

    def _get_interaction_partner_domain(self, partner):
        return [
            ("email", "=", partner.email),
            ("email", "!=", False),
        ]
