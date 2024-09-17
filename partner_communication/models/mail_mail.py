##############################################################################
#
#    Copyright (C) 2024 Compassion CH (https://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re
from email.header import Header
from functools import reduce

from odoo import api, fields, models


def _sanitize_subject(subject):
    """
    Sanitize the email subject line by removing characters that are not compliant
    with RFC 2822.

    Args:
        subject (str): the original email subject

    Returns:
        str: the sanitized email subject
    """

    # Remove all line breaks (newlines, carriage returns)
    subject = re.sub(r"[\r\n]+", " ", subject)

    # Remove extra whitespace
    subject = subject.strip()

    # Encode the subject to ensure RFC 2822 compliance
    header = Header(subject, "utf-8")
    sanitized_subject = str(header)

    return sanitized_subject


class MailMail(models.Model):
    """Override the create method to sanitize the email"""

    _inherit = "mail.mail"

    communication_config_id = fields.Many2one(
        "partner.communication.config",
        "Communication type",
    )

    def send(self, auto_commit=False, raise_exception=False):
        """Create communication for partner, if not already existing."""
        comm_obj = (
            self.env["partner.communication.job"]
            .with_context({})
            .with_context(no_print=True)
        )
        config = self.env.ref("partner_communication.default_communication")
        for email in self.exists().filtered(
            lambda e: e.mail_message_id.model != "partner.communication.job"
        ):
            communication = comm_obj.search([("email_id", "=", email.id)])
            if not communication:
                for partner in email.recipient_ids.filtered(
                    lambda p: not p.user_ids
                    or reduce(lambda u1, u2: u1 and u2, p.user_ids.mapped("share"))
                ):
                    comm_obj.create(
                        {
                            "config_id": config.id,
                            "partner_id": partner.id,
                            "user_id": email.author_id.user_ids.id,
                            "object_ids": email.recipient_ids.ids,
                            "state": "done",
                            "auto_send": False,
                            "email_id": email.id,
                            "sent_date": fields.Datetime.now(),
                            "body_html": email.body_html,
                            "subject": email.subject,
                            "ir_attachment_ids": [(6, 0, email.attachment_ids.ids)],
                        }
                    )
        return super().send(auto_commit, raise_exception)

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if "subject" in values and values["subject"]:
                values["subject"] = _sanitize_subject(values["subject"])

        return super().create(values_list)
