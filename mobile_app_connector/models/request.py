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
from odoo.tools import config

logger = logging.getLogger(__name__)
try:
    import detectlanguage
except ImportError:
    logger.warning("Please install detectlanguage")


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

        partner = self.sudo().env['res.partner'].search([('email', 'like', email)])

        claim = self.sudo().create({
            'email_from': email,
            'subject': subject,
            'code':
                self.env.ref('mobile_app_connector.sequence_claim_app')
                    .sudo()._next(),
            'name': question,
            'categ_id': self.env['crm.claim.category'].sudo().search(
                [('name', '=', source)]).id,
            'partner_id': contact_id or partner.id,
            'user_id': False,
            'language': self.sudo().detect_lang(question).lang_id.code
        })
        claim.message_post(body=question,
                           subject=_("Original request from %s %s ") %
                           (firstname, lastname))
        if partner:
            self.sudo().create_email_for_interaction_resume(subject, question, partner)

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

    @api.model
    def detect_lang(self, text):
        """
        Use detectlanguage API to find the language of the given text
        :param text: text to detect
        :return: res.lang compassion record if the language is found, or False
        """
        detectlanguage.configuration.api_key = config.get(
            'detect_language_api_key')
        language_name = False
        langs = detectlanguage.languages()
        try:
            code_lang = detectlanguage.simple_detect(text)
        except (IndexError, detectlanguage.DetectLanguageError):
            # Language could not be detected
            return False
        for lang in langs:
            if lang.get("code") == code_lang:
                language_name = lang.get("name")
                break
        if not language_name:
            return False

        return self.env['res.lang.compassion'].search(
            [('name', '=ilike', language_name)], limit=1)
