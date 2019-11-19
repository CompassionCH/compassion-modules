##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)

import html.parser

BOX_SEPARATOR = '#BOX#'
PAGE_SEPARATOR = '#PAGE#'


class CorrespondencePage(models.Model):
    """ This class defines a page used for in sponsorship correspondence"""

    _inherit = "compassion.mapped.model"
    _name = 'correspondence.page'
    _description = 'Letter page'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    correspondence_id = fields.Many2one(
        'correspondence', ondelete='cascade', required=True)

    original_page_url = fields.Char()
    final_page_url = fields.Char()
    original_text = fields.Text(default='')
    english_text = fields.Text(default='', oldname='english_translated_text')
    translated_text = fields.Text(default='')

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    _sql_constraints = [
        ('original_page_url',
         'unique(original_page_url)',
         _('The pages already exists in database.')),
        ('final_page_url',
         'unique(final_page_url)',
         _('The pages already exists in database.')),
    ]

    def format_text(self, text):
        return text and text.split('\n' + BOX_SEPARATOR + '\n') or ['']

    @api.multi
    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)
        json_data['OriginalText'] = lambda text: self.format_text(text)
        return json_data

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        html_parser = html.parser.HTMLParser()
        fields = ('original_text', 'english_text', 'translated_text')
        for field in fields:
            if field in odoo_data:
                odoo_data[field] = html_parser.unescape(BOX_SEPARATOR.join(
                    odoo_data[field]))
        return odoo_data
