# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from base_mapping import OnrampMapping
from openerp.addons.sbc_compassion.models.correspondence_page import \
    BOX_SEPARATOR


class PageMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field names
    for the model Sponsorship Correspondence.

    All fields are described at
    http://developer.compassion.com/docs/read/compassion_connect2/
    Communication_Kit_Fields_and_Sample_JSON
    """
    ODOO_MODEL = 'correspondence.page'

    CONNECT_MAPPING = {
        'OriginalPageURL': 'original_page_url',
        'FinalPageURL': 'final_page_url',
        'OriginalText': 'original_text',
        'EnglishTranslatedText': 'english_translated_text',
        'TranslatedText': 'translated_text'
    }

    FIELDS_TO_SUBMIT = {
        'OriginalPageURL': None,
        'FinalPageURL': None,
        'OriginalText': None,
        'EnglishTranslatedText': None,
        'TranslatedText': None
    }

    def _process_connect_data(self, connect_data):
        fields = (
            'OriginalText', 'EnglishTranslatedText', 'TranslatedText')
        for field in fields:
            if field in connect_data:
                connect_data[field] = [connect_data[field]]

    def _process_odoo_data(self, odoo_data):
        # Concatenation of all boxes in one text
        fields = (
            'original_text', 'english_translated_text', 'translated_text')
        for field in fields:
            if field in odoo_data:
                odoo_data[field] = BOX_SEPARATOR.join(odoo_data[field])
