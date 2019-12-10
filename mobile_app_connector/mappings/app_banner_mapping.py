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


class AppBannerMapping(OnrampMapping):
    ODOO_MODEL = 'mobile.app.banner'
    MAPPING_NAME = 'mobile_app_banner'

    CONNECT_MAPPING = {
        'HERO_TITLE': 'name',
        'HERO_DESCRIPTION': 'body',
        'HERO_IMAGE': 'image_url',
        'HERO_CTA_TEXT': 'button_text',
        'HERO_CTA_DESTINATION': 'internal_action',
        'HERO_CTA_DESTINATION_TYPE': 'destination_type',
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    CONSTANTS = {
        'IS_DELETED': '0',
        'BLOG_DISPLAY_TYPE': 'Tile',
    }

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        res = super(AppBannerMapping, self).get_connect_data(
            odoo_object, fields_to_submit)
        if odoo_object.destination_type == 'External':
            # Replace destination with URL
            res['HERO_CTA_DESTINATION'] = odoo_object.external_url
        res['BLOG_DISPLAY_TYPE'] = 'Tile'
        return res
