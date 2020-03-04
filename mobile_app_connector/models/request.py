##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import cgi

from odoo import models, api, _, fields
from odoo.tools import html_escape as escape

logger = logging.getLogger(__name__)


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.multi
    def mobile_contact_us(self, parameters, **params):
        """
        End point for the "Contact Us" page of the Android and iOS apps.
        :param parameters: dictionary containing
                                email
                                firstname
                                lastname
                                question
                                subject
                                source
                            and possibly contact_id
        :param params: no value expected
        :return: a dict with key FeedbackAndContactusResult
        """
        for key in parameters:
            parameters[key] = cgi.escape(parameters[key])

        email = parameters["email"]
        firstname = parameters["firstname"]
        lastname = parameters["lastname"]
        question = parameters["question"]
        subject = parameters["subject"]
        source = parameters["source"]
        if "contactid" in parameters:
            contact_id = parameters["contactid"]
        else:
            contact_id = None

        claim = self.sudo().create({
            'email_from': email,
            'subject': subject,
            'code':
                self.env.ref('mobile_app_connector.sequence_claim_app')
                    .sudo()._next(),
            'name': question,
            'categ_id': self.env['crm.claim.category'].sudo().search(
                [('name', '=', source)]).id,
            'partner_id': contact_id,
            'user_id': False
        })
        claim.message_post(body=question,
                           subject=_("Original request from %s %s ") %
                           (firstname, lastname))

        if contact_id:
            partner = self.env['res.partner'].browse(int(contact_id))
            if partner.exists():
                self.create_email_for_interaction_resume(subject, question, partner)

        return {
            "FeedbackAndContactusResult": _("Your question was well received")
        }

    def create_email_for_interaction_resume(self, subject, body, partner):
        """
        Creates a mail to make the new request appear on the interaction resume
        :param subject: subject of email
        :param body: body of email
        :param message: mail.message
        :param partner: partner making the request
        :return: None
        """
        self.env['mail.mail'].create({
            'state': 'sent',
            'subject': subject,
            'body_html': body,
            'author_id': partner.id,
            'email_from': partner.email,
            'mail_message_id': self.env['mail.message'].create({
                'model': 'res.partner',
                'res_id': partner.id,
                'body': escape(body),
                'subject': subject,
                'author_id': partner.id,
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'date': fields.Datetime.now(),
            }).id
        })
