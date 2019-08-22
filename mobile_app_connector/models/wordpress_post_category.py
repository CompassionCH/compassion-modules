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


class WordpressPostCategory(models.Model):
    """
    This serves as a local cache of all Published articles on the WP website,
    in order to answer fast to mobile app queries for rendering the main
    hub of the users.
    """
    _name = 'wp.post.category'
    _description = 'Wordpress post category'

    name = fields.Char(required=True)
    order_weight = fields.Integer(
        default=1000,
        help='Decrease order weight to display tiles above others'
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'This category already exists')
    ]
