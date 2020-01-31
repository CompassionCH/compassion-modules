# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>, Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _
import datetime
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileCorrespondenceMapping(OnrampMapping):
    ODOO_MODEL = 'correspondence'
    MAPPING_NAME = 'mobile_app_correspondence'

    CONNECT_MAPPING = {
        'actionid': ('sponsorship_id.id', 'recurring.contract'),
        'TemplateID': ('template_id.id', 'correspondence.template'),
        'TemplateName': ('template_id.name', 'correspondence.template'),
        'Message': 'original_text',
        'MessageTo': None,
        'MessageFrom': None,
        'Need': ('sponsorship_id.child_id.local_id', 'compassion.child'),
        'Supportergroup': None,
        'supporterId': ('sponsorship_id.partner_id.id', 'res.partner'),
        'pathextension': 'letter_format',
        'base64string': 'b64image'
    }


class FromLetterMapping(OnrampMapping):
    ODOO_MODEL = 'correspondence'
    MAPPING_NAME = 'mobile_app_from_letter'

    CONNECT_MAPPING = {
        'CorrespondenceID': 'id',
        'Date': "status_date",
        'FileID': 'id',  # Can be a string? int in example
        'FileName': "file_name",
        'Message': 'original_text',
    }

    FIELDS_TO_SUBMIT = {
        'CorrespondenceID': None,
        'Date': lambda date: datetime.datetime.strptime(
            date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S'),
        'FileID': None,  # Can be a string? int in example
        'FileName': None,
        'Message': None,
    }

    # FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        mapped = super(FromLetterMapping, self) \
            .get_connect_data(odoo_object, fields_to_submit)
        mapped['Type'] = 1  # todo figure out what to use here
        if not mapped['Message']:
            mapped['Message'] = _("Physical letters cannot be displayed.")
        return mapped
