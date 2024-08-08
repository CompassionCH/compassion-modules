import re

from odoo import fields, models
from odoo.tools.mail import html2plaintext


class MailingTrace(models.Model):
    _inherit = ["mailing.trace", "interaction.source"]
    _name = "mailing.trace"

    date = fields.Datetime(related="sent", search="_search_date")

    def _search_date(self, operator, value):
        return [("sent", operator, value)]

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
                "date": rec.sent,
                "email": rec.email,
                "communication_type": "Mass",
                "subject": rec.mass_mailing_id.subject,
                "body": rec._get_body(),
                "has_attachment": bool(rec.mail_mail_id.attachment_ids),
                "tracking_status": rec.mail_tracking_id.state
                if rec.mail_tracking_id
                else rec.state,
            }
            for rec in self
        ]

    def _get_interaction_partner_domain(self, partner):
        return [
            ("email", "=", partner.email),
        ]
