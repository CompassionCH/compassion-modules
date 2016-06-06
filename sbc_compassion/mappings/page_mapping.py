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
from HTMLParser import HTMLParser

from base_mapping import OnrampMapping
from openerp.addons.sbc_compassion.models.correspondence_page import \
    BOX_SEPARATOR


def _format_text(text):
        return text and text.split('\n' + BOX_SEPARATOR + '\n') or ['']


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
        'OriginalText': lambda text: _format_text(text),
        'EnglishTranslatedText': lambda text: _format_text(text),
        'TranslatedText': lambda text: _format_text(text)
    }

    def _process_odoo_data(self, odoo_data):
        # Concatenation of all boxes in one text
        html_parser = HTMLParser()
        fields = (
            'original_text', 'english_translated_text', 'translated_text')
        for field in fields:
            if field in odoo_data:
                odoo_data[field] = html_parser.unescape(BOX_SEPARATOR.join(
                    odoo_data[field]))
