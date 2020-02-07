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
    _inherit = 'compassion.mapped.model'
    _order = 'state asc, print_count asc, date_start asc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('Title', translate=True, required=True)
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
    external_url = fields.Char(translate=True)
    date_start = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    date_stop = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    active = fields.Boolean(oldname='is_active', default=True)
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
    @api.depends('active')
    def _compute_state(self):
        for banner in self:
            if banner.active:
                banner.state = 'active'
            else:
                banner.state = 'used' if banner.print_count else 'new'

    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for banner in self:
            date_start = fields.Date.from_string(banner.date_start)
            date_stop = fields.Date.from_string(banner.date_stop)
            if date_start and date_stop and date_stop <= date_start:
                raise ValidationError(_("Period is not valid"))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def validity_cron(self):
        today = fields.Date.today()
        active_banners = self.search([])
        current_banners = self.search([
            ('date_start', '<=', today),
            ('date_stop', '>=', today),
        ])
        without_dates_banners = self.search([
            ('date_start', '=', None),
            ('date_stop', '=', None),
        ])
        # Deactivate old stories
        (active_banners - current_banners - without_dates_banners).write(
            {'active': False})
        # Activate current stories
        current_banners.write({'active': True})

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        res['IS_DELETED'] = "0"
        res['BLOG_DISPLAY_TYPE'] = "Tile"
        for key, value in list(res.items()):
            if not value:
                res[key] = None
        return res