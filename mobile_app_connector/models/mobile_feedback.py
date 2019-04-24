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
from odoo import models, fields, _

logger = logging.getLogger(__name__)


class AppBanner(models.Model):
    _name = 'mobile.app.feedback'
    _description = 'Mobile App Feedback'
    _order = 'id desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('What did you like', translate=True, required=True,
                       readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    improve_app = fields.Char(translate=True, readonly=True)
    source = fields.Char(translate=True, readonly=True)
    star = fields.Selection([
        ('1.0', 'disappointing'),
        ('2.0', 'Well'),
        ('3.0', 'very well'),
        ('4.0', 'Great'),
        ('5.0', 'Extraordinary')], select=True, readonly=True)
    create_date = fields.Datetime(
        string='Creation Date',
        readonly=True,
        default=datetime.today(),
    )
