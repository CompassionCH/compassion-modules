# Copyright (C) 2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import html

from odoo import models, _


class MailMessage(models.Model):
    """
    Extend the mail composer so that it can send message to archived partner,
    and put back the selected partner in the claim in case it was not linked.
    """

    _inherit = "mail.message"

    def get_message_quote(self):
        """
        Helper to quote a message from another. This will return the message
        formatted for quoting.
        :return: HTML of quotted message
        """
        self.ensure_one()
        lib_subject = _("Subject")
        lib_from = _("From")
        lib_message = _("Original Message")
        header1 = '<div style="font-size:10pt;color:#1f497d">' "<br></div>"
        header2 = '<div style="font-size:10pt;color:#500050;">'
        header3 = "----" + lib_message + "----"
        br = "<br />"

        email_from = "no-email"
        if self.email_from:
            email_from = self.email_from
        email_from = (
            "<b>"
            + lib_from
            + "</b>:"
            + str(html.escape(email_from).encode("ascii", "xmlcharrefreplace"))
        )
        mail_date = "<b>Date</b>:" + str(self.date)
        body = ""
        if self.body and self.body != "":
            body = self.body.replace("#1f497d", "#500050") + "</div>"
        subject = "<b>" + lib_subject + "</b>:"
        if self.subject and self.subject != "":
            subject = (
                "<b>"
                + lib_subject
                + "</b>:"
                + str(
                    html.escape(self.subject).encode("ascii", "xmlcharrefreplace")
                    or self.record_name
                    or ""
                )
            )

        return (
            header1
            + header2
            + header3
            + br
            + str(email_from)
            + br
            + subject
            + br
            + mail_date
            + 2 * br
            + body
        )
