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


class TileMapping(OnrampMapping):
    ODOO_MODEL = 'mobile.app.tile'
    MAPPING_NAME = 'mobile_app_tile'

    CONNECT_MAPPING = {
        'Body': 'body',
        'ActionText': 'action_text',
        'Title': 'title',
        'SubType': 'subtype_id.code',
        'SortOrder': 'view_order',
        'ActionDestination': 'action_destination',
        'Type': ('subtype_id.type_id.code', 'mobile.app.tile.type'),
    }

    FIELDS_TO_SUBMIT = {
        'Body': unicode,
        'ActionText': unicode,
        'Title': unicode,
        'SubType': None,
        'SortOrder': None,
        'ActionDestination': None,
        'Type': None,
    }
