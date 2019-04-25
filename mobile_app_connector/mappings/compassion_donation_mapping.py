# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileDonationMapping(OnrampMapping):
    ODOO_MODEL = 'product.template'
    MAPPING_NAME = 'mobile_app_donation'

    CONNECT_MAPPING = {
        "DisplayOrder": "id",
        "FundName": "name",
        "Id": "id",
        "ImageIcon": "image_icon",
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    def _process_connect_data(self, connect_data):
        for key, value in connect_data.copy().iteritems():
            if key == "FundName":
                if value:
                    connect_data[key] = value
        return connect_data
