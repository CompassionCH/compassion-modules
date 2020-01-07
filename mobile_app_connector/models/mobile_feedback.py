# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Tarabbia
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import datetime
from odoo import models, fields, api

logger = logging.getLogger(__name__)


class MobileFeedback(models.Model):
    _name = 'mobile.app.feedback'
    _description = 'Mobile App Feedback'
    _order = 'id desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('What did you like', required=True,
                       readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    language = fields.Selection('_get_lang')
    improve_app = fields.Char('How can we improve the app', readonly=True)
    source = fields.Selection([
        ('Android', 'Android'),
        ('iOS', 'iOS')], readonly=True)
    star = fields.Selection([
        ('0.0', 'None'),
        ('1.0', 'Disappointing'),
        ('2.0', 'Well'),
        ('3.0', 'Very well'),
        ('4.0', 'Great'),
        ('5.0', 'Extraordinary')], readonly=True)
    create_date = fields.Datetime(
        string='Creation Date',
        readonly=True,
        default=datetime.today(),
    )

    @api.model
    def _get_lang(self):
        langs = self.env['res.lang'].search([])
        return [(l.code, l.name) for l in langs]

    def mobile_feedback(self, data=None, **parameters):
        star = str(float(parameters.get('star', 3.0)))
        what_did_u_like = parameters.get('Whatdidulike', '-')
        # source parameter is not defined in ios application
        source = parameters.get('source', 'iOS')
        improve_app = parameters.get('Improveapp', '-')
        record = self.create({
            'name': what_did_u_like,
            'partner_id': self.env.user.partner_id.id,
            'source': source,
            'improve_app': improve_app, 'star': star
        })
        if 'lang' in self.env.context:
            record['language'] = self.env.context['lang']

        return record.id
