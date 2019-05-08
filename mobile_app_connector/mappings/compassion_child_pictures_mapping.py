# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileChildPicturesMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.child.pictures'
    MAPPING_NAME = 'mobile_app_child_pictures'

    CONNECT_MAPPING = {
        'Date': 'date',
        'Url': 'image_url',
        'OrderDate': 'date',
    }

    FIELDS_TO_SUBMIT = {
        'Date': lambda date: datetime.datetime.strptime(
            date, '%Y-%m-%d').strftime('%d-%m-%Y %H:%M:%S'),
        'Url': None,
        'OrderDate': None,
    }

    # FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}
