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
import cgi

from odoo import models, api, _

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
                self.env.ref('crm_claim_code.sequence_claim_app')
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

        return {
            "FeedbackAndContactusResult": _("Your question was well received")
        }
