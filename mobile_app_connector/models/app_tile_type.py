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

from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class AppTileType(models.Model):
    _name = 'mobile.app.tile.type'
    _description = 'Tile type'
    _order = 'view_order'

    name = fields.Char('Description', required=True)
    code = fields.Char(required=True)
    view_order = fields.Integer('View order', required=True)
    subtype_ids = fields.One2many(
        'mobile.app.tile.subtype', 'type_id', 'Subtypes')
    param_1 = fields.Char('first parameter')
    param_2 = fields.Char('second parameter')
    param_3 = fields.Char('third parameter')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'This tile type already exists')
    ]


class AppTileSubtype(models.Model):
    _name = 'mobile.app.tile.subtype'
    _description = 'Tile subtype'

    name = fields.Char('Description', required=True)
    code = fields.Char(required=True)
    view_order = fields.Integer('View order', required=True)
    type_id = fields.Many2one('mobile.app.tile.type', required=True)
    tile_preview = fields.Binary(attachment=True)
    default_model_id = fields.Many2one(
        'ir.model', "Default model", help="Select related objects type")
    default_model = fields.Char(related='default_model_id.model')
    default_title = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records.")
    default_body = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records."
    )
    default_action_text = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records."
    )
    default_action_destination = fields.Selection(
        'select_action_destination', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'This subtype already exists')
    ]

    @api.model
    def select_action_destination(self):
        return [
            ('Youtube video opens', _('Youtube')),
            ('Login overlay', _('Login')),
            ('Stories and prayer with relevant blog at the top', _('Blog')),
            ('Child selector', _('Child selector')),
            ('Compass', _('Child compass')),
            ('Top of letters hub', _('Letters hub')),
            ('Give overlay', _('Fund donation')),
            ('Give a gift overlay', _('Child gift')),
            ('Feedback overlay', _('Feedback form')),
            ('Photos overlay', _('Child photos')),
            ('Read overlay', _('Child letter')),
            ('My Community', _('Project page')),
            ('Individual child page', _('Child page'))
        ]
