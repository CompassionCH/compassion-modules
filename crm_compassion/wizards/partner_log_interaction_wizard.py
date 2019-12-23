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
    _name = 'partner.log.interaction.wizard'
    _description = "Logging wizard for interactions"

    partner_id = fields.Many2one(
        'res.partner', 'Partner', default=lambda s: s._default_partner())
    subject = fields.Char()
    body = fields.Html()

    @api.model
    def _default_partner(self):
        # Get the partner from context
        return self.env.context.get('active_id')

    def log_interaction(self):
        """
        Create an e-mail in the 'sent' state (without sending the e-mail)
        in order for it to appear in the interaction.resume view
        :return: True
        """
        return self.env['mail.mail'].create({
            'state': 'sent',
            'recipient_ids': [(4, self.partner_id.id)],
            'subject': self.subject,
            'body_html': self.body,
            'author_id': self.env.user.partner_id.id,
            'mail_message_id': self.env['mail.message'].create({
                'model': 'res.partner',
                'res_id': self.partner_id.id,
                'body': self.body,
                'subject': self.subject,
                'author_id': self.env.user.partner_id.id,
                'subtype_id': self.env.ref('mail.mt_comment').id
            }).id
        })
