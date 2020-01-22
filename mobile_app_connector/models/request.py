# -*- coding: utf-8 -*-
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

from odoo import models, api, _
from datetime import datetime
from odoo.tools import html_escape as escape

logger = logging.getLogger(__name__)


class CrmClaim(models.Model):
    """ A sponsored child """
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
                self.env.ref('crm_claim_code.sequence_claim_app')
                    .sudo()._next(),
            'name': question,
            'categ_id': self.env['crm.claim.category'].sudo().search(
                [('name', '=', source)]).id,
            'partner_id': contact_id,
        })
        claim.message_post(body=question,
                           subject=_("Original request from %s %s ") %
                           (firstname, lastname))

        partner = self.env['res.partner'].browse(int(contact_id))
        if partner:
            self.create_email_for_interaction_resume(subject, question, partner)

        return {
            "FeedbackAndContactusResult": _("Your question was well received")
        }

    def create_email_for_interaction_resume(self, subject, body, partner):
        """
        Creates a mail to make the new request appear on the interaction resume
        :param subject: subject of email
        :param body: body of email
        :param partner: partner making the request
        :return: None
        """
        mail = self.env['mail.mail'].create({
            'state': 'sent',
            # 'recipient_ids': [(4, contact_id)],
            'subject': subject,
            'body_html': body,
            'author_id': partner.id,
            'email_from': partner.email,
            'sent_date': datetime.today(),
            'mail_message_id': self.env['mail.message'].create({
                'model': 'res.partner',
                'res_id': partner.id,
                'body': escape(body),
                'subject': subject,
                'author_id': partner.id,
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'date': datetime.today(),
            }).id
        })

        self.env['mail.tracking.email'].sudo().create({
            'mail_id': mail.id,
            'recipient_address': partner.email,
            'partner_id': partner.id
        })

        config = self.env.ref('partner_communication.default_communication')
        self.env['partner.communication.job'].sudo().create({
            'partner_id': partner.id,
            'config_id': config.id,
            'auto_send': False
        })
