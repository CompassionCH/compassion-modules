# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


class AppBanner(models.Model):
    _name = 'mobile.app.banner'
    _description = 'Mobile App Banner'
    _order = 'state asc, print_count asc, date_start asc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('Title', translate=True, required=True)
    type = fields.Selection([
        ('WithoutLogin', 'Public'),
        ('Default', 'Logged In'),
        ('Default and WithoutLogin', 'Both'),
    ], default='WithoutLogin', required=True)
    destination_type = fields.Selection([
        ('Internal', 'Internal'),
        ('External', 'Open in web browser')
    ], required=True)
    internal_action = fields.Selection([
        ('Pray', 'My prayers'),
        ('Donation', 'Donation'),
        ('Letter', 'Letter writing'),
        ('Blog', 'Blog'),
        # we disable this as it behaves the same as Blog:
        # ('Prayer', 'Prayers hub'),
        # ('News', 'News'),
    ])
    button_text = fields.Char(translate=True)
    body = fields.Text(translate=True)
    image_url = fields.Char(translate=True)
    date_start = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    date_stop = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    is_active = fields.Boolean()
    state = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('used', 'Used')
    ], compute='_compute_state', store=True, default='new')
    print_count = fields.Integer(readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('is_active')
    def _compute_state(self):
        for banner in self:
            if banner.is_active:
                banner.state = 'active'
            else:
                banner.state = 'used' if banner.print_count else 'new'

    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for banner in self.filtered(lambda s: s.type == 'story'):
            date_start = fields.Date.from_string(banner.date_start)
            date_stop = fields.Date.from_string(banner.date_stop)
            if date_stop <= date_start:
                raise ValidationError(_("Period is not valid"))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def validity_cron(self):
        today = fields.Date.today()
        active_banners = self.search([
            ('is_active', '=', True),
        ])
        current_banners = self.search([
            ('date_start', '<=', today),
            ('date_stop', '>=', today),
        ])
        # Deactivate old stories
        (active_banners - current_banners).write({'is_active': False})
        # Activate current stories
        current_banners.write({'is_active': True})
