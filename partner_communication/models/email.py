# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import api, models, fields


class Email(models.Model):
    """ Add relation to communication configuration to track generated
    e-mails.
    """
    _inherit = 'mail.mail'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    communication_config_id = fields.Many2one('partner.communication.config')

    @api.multi
    def send(self, auto_commit=False, raise_exception=False):
        """ Create communication for partner, if not already existing.
        """
        super(Email, self).send(auto_commit, raise_exception)
        comm_obj = self.env['partner.communication.job'].with_context(
            no_print=True, default_attachment_ids=False)
        config = self.env.ref(
            'partner_communication.default_communication')
        for email in self:
            communication = comm_obj.search([('email_id', '=', email.id)])
            if not communication:
                for partner in email.recipient_ids:
                    comm_obj.create({
                        'config_id': config.id,
                        'partner_id': partner.id,
                        'user_id': self.env.uid,
                        'object_ids': email.recipient_ids.ids,
                        'state': 'done',
                        'email_id': email.id,
                        'sent_date': fields.Datetime.now(),
                        'body_html': email.body_html,
                        'subject': email.subject,
                        'ir_attachment_ids': [(6, 0, email.attachment_ids.ids)]
                    })
