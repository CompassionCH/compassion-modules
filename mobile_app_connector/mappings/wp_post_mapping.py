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
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class WPPostMapping(OnrampMapping):
    ODOO_MODEL = 'wp.post'
    MAPPING_NAME = 'mobile_app_wp_post'

    CONNECT_MAPPING = {
        'Blog': {
            'ImageUrl': 'image_url',
            'Title': 'name',
            'Url': 'url',
            'WP_id': 'wp_id',
            'Post_type': 'post_type',
        },
        'Title': 'name',
        'ActionText': 'name',
        'SortOrder': 'view_order',
        'IsAutomaticOrdering': 'is_automatic_ordering',
        'OrderDate': 'date',
        'Type': 'tile_type',
        'SubType': 'tile_subtype'
    }

    FIELDS_TO_SUBMIT = {
        'Blog.ImageUrl': None,
        'Blog.Title': None,
        'Blog.Url': None,
        'Blog.WP_id': None,
        'Blog.Post_type': None,
        'Title': None,
        'ActionDestination': None,
        'Type': None,
        'SubType': None,
        'ActionText': None,
        'SortOrder': None,
        'IsAutomaticOrdering': None,
        'OrderDate': None,
    }

    CONSTANTS = {
        'ActionDestination': 'Stories and prayer with relevant blog at '
                             'the top'
    }
