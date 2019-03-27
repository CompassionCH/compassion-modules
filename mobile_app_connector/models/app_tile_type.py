# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class AppTileType(models.Model):
    _name = 'mobile.app.tile.type'
    _description = 'Type tile'
    _order = 'view_order'
    _rec_name = 'libelle'

    code = fields.Char(required=True, index=True)
    libelle = fields.Char('Title', required=True)

    enabled = fields.Boolean('Active', default=True,
                             help='enable/disable type', index=True)

    subject_standard = fields.Char('Title standard')

    body_standard = fields.Html(string='Body standard',
                                help='Enter the content of '
                                'the template for this category')

    view_order = fields.Integer('View order', required=True, index=True)

    param_1 = fields.Char('first parameter')

    param_2 = fields.Char('second parameter')

    param_3 = fields.Char('third parameter')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'This tile type already exists')
    ]
