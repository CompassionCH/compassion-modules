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
            'Url': 'url'
        },
        'Title': 'name',
    }

    FIELDS_TO_SUBMIT = {
        'Blog.ImageUrl': None,
        'Blog.Title': None,
        'Blog.Url': None,
        'Title': None,
        'ActionDestination': None,
        'Type': None,
        'SubType': None,
    }

    CONSTANTS = {
        'ActionDestination': 'Stories and prayer with relevant blog at '
                             'the top',
        'Type': 'Story',
        # TODO See if we must change subtype depending on post
        'SubType': 'ST_T1'
    }
