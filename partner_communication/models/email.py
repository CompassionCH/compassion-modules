##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from functools import reduce

from odoo import api, models, fields


class Email(models.Model):
    """ Add relation to communication configuration to track generated
    e-mails.
    """

    _inherit = "mail.mail"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    communication_config_id = fields.Many2one(
        "partner.communication.config", readonly=False
    )

    def send(self, auto_commit=False, raise_exception=False):
        """ Create communication for partner, if not already existing.
        """
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
                        or reduce(lambda u1, u2: u1 and u2,
                                  p.user_ids.mapped("share"))
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
