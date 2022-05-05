##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class LogInteractionWizard(models.TransientModel):
    _name = "partner.log.interaction.wizard"
    _description = "Logging wizard for interactions"

    partner_id = fields.Many2one(
        "res.partner", "Partner", default=lambda s: s._default_partner(), readonly=False
    )
    subject = fields.Char()
    date = fields.Datetime(default=fields.Datetime.now)
    body = fields.Html()
    direction = fields.Selection(
        [("in", "Incoming"), ("out", "Outgoing"), ], default='out', required=True
    )

    @api.model
    def _default_partner(self):
        # Get the partner from context
        return self.env.context.get("active_id")

    def log_interaction(self):
        """
        Create an e-mail in the 'sent' state (without sending the e-mail)
        in order for it to appear in the interaction.resume view
        :return: True
        """
        user = self.env.user
        partner = self.partner_id
        mail = self.env["mail.mail"].create(
            {
                "state": "sent",
                "recipient_ids": [(4, partner.id if self.direction == "out" else user.partner_id.id)],
                "subject": self.subject,
                "body_html": self.body,
                "author_id": user.partner_id.id
                if self.direction == "out" else partner.id,
                "is_from_employee": self.direction == "out",
                "direction": self.direction,
                "date": self.date,
                "mail_message_id": self.env["mail.message"]
                .create({
                    "model": "res.partner",
                    "res_id": partner.id,
                    "body": self.body,
                    "subject": self.subject,
                    "author_id": user.partner_id.id
                    if self.direction == "out" else partner.id,
                    "subtype_id": self.env.ref("mail.mt_comment").id,
                    "email_from": user.email if self.direction == "out" else
                    partner.email,
                    "date": self.date
                }).id,
            }
        )
        # Create the mail.tracking.email object in the case of a manually logged email
        email = mail._send_prepare_values(partner=partner)
        vals = mail._tracking_email_prepare(partner, email)
        vals.update({
            "state": "sent"
        })
        mail_tracking_obj = self.env['mail.tracking.email']
        mail_tracking_obj.search([
            ('mail_id', '=', mail.id)
        ]).unlink()
        mail_tracking_obj.sudo().create(vals)
