# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Tarabbia <j.tarabbia@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from ..tools import wp_requests


from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class AppTile(models.Model):
    # internal field Odoo
    _name = 'mobile.app.tile'
    _description = 'Tile'
    _order = 'view_order'
    _rec_name = 'subject'

    # Fields of class
    priority = fields.Selection([
        ('High', 'High'),
        ('Normal', 'Normal'),
        ('Low', 'Low')
    ], 'Priority', default='Normal', required=True)

    sub_type = fields.Selection([
        ('LE-T1', 'LE-T1'),
        ('LE-T2', 'LE-T2'),
        ('LE-1', 'LE-1'),
        ('LE-T3', 'LE-T3'),
        ('PR1', 'PR1'),
        ('PR2', 'PR2'),
        ('PR-T2', 'PR-T1'),
        ('CO1', 'CO1'),
        ('CO2', 'CO2'),
        ('CO3', 'CO3'),
        ('ST-T1/T2', 'ST-T1/T2'),
        ('ST1', 'ST1'),
        ('GI3', 'GI3'),
        ('GI-T1', 'GI-T1'),
        ('GI1', 'GI1'),
        ('CH1', 'CH1'),
        ('tbc', 'tbc'),
        ('CH2', 'CH2'),
        ('CH-T1', 'CH-T1'),
        ('MI1', 'MI1'),
        ('MI2', 'MI2')
    ], 'SubType', required=True)

    subject = fields.Char('Title', required=True)

    type_id = fields.Many2one('mobile.app.tile.type', 'Type', required=True, index=True,
                              help='Type & sub-type')

    date_debut = fields.Datetime('Start activation date', required=True)

    date_fin = fields.Datetime('End activation date')

    action_destination = fields.Selection([
        ('Youtube video opens', 'Youtube video opens'),
        ('Login overlay', 'Login overlay'),
        ('Stories and prayer with relevant blog at the top', 'Stories and prayer with relevant blog at the top'),
        ('Child selector', 'Child selector'),
        ('Compass', 'Compass'),
        ('Top of letters hub', 'Top of letters hub'),
        ('Give overlay', 'Give overlay'),
        ('Give a gift overlay', 'Give a gift overlay'),
        ('Feedback overlay', 'Feedback overlay'),
        ('Photos overlay', 'Photos overlay'),
        ('Read overlay', 'Read overlay'),
        ('My Community', 'My Community'),
        ('Individual child page', 'Individual child page')], 'Action destination', required=True)

    action_text = fields.Char('Action text', required=True)

    body = fields.Html(string='Body',
                       help='Enter the content of the message')

    view_order = fields.Integer('View order', required=True, index=True)

    enabled = fields.Selection([
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], 'State', default='Active', required=True)

    param_1 = fields.Char(
        'first parameter',
        related='type_id.param_1',
        readonly=True)
    param_2 = fields.Char(
        'second parameter',
        related='type_id.param_2',
        readonly=True)
    param_3 = fields.Char(
        'third parameter',
        related='type_id.param_3',
        readonly=True)

    # Constraints
    _sql_constraints = [
        ('subject_unique', 'unique(subject)', 'This title already exists')
    ]

    @api.onchange('type_id')
    def _onchange_partner(self):
        if not self.body:
            self.body = "%s" % (self.type_id.body_standard or "")
        if not self.subject:
            self.subject = "%s" % (self.type_id.subject_standard or "")
