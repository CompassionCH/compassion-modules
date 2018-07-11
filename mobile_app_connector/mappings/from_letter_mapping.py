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
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class FromLetterMapping(OnrampMapping):
    ODOO_MODEL = 'correspondence'
    MAPPING_NAME = 'mobile_app_from_letter'

    CONNECT_MAPPING = {
        'CorrespondenceID': 'id',
        'DateProcessed': "status_date",
        'FileID': 'uuid',  # Can be a string? int in example
        'FileName': "file_name",
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        mapped = super(FromLetterMapping, self) \
            .get_connect_data(odoo_object, fields_to_submit)
        mapped['Type'] = 1 # todo figure out what to use here
        return mapped
