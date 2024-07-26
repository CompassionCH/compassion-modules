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

from odoo import api, models


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

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if "subject" in values:
                values["subject"] = _sanitize_subject(values["subject"])

        return super().create(values_list)
