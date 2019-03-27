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
        'Title': 'subject',
        'SubType': 'sub_type',
        'SortOrder': 'view_order',
        'ActionDestination': 'action_destination',
        'Type': ('type_id.libelle', 'mobile.app.tile.type'),
    }

    FIELDS_TO_SUBMIT = {
        'Body': None,
        'ActionText': None,
        'Title': None,
        'SubType': None,
        'SortOrder': None,
        'ActionDestination': None,
        'Type': None,
    }
