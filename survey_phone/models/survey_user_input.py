# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, fields
from odoo.addons.base_phone import fields as phone_fields
logger = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    """
    Add some fields to the answer view for a survey. In particular a filed for
    both mobile and phone number as well as a clickable URL to the survey page.
    """
    _inherit = 'survey.user_input'
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 readonly=False)
    phone = phone_fields.Phone(related='partner_id.phone')
    mobile = phone_fields.Phone(related='partner_id.mobile')
    survey_link = fields.Char("Link to complete the survey",
                              compute='_compute_survey_link')

    def _compute_survey_link(self):
        """
        Recreate the private url to access the survey from the token and public
        url available in self.
        :return: Nothing
        """
        self.survey_link = self.survey_id.public_url + '/' + self.token
