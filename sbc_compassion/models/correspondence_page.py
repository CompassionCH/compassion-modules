# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _

BOX_SEPARATOR = '#BOX#'
PAGE_SEPARATOR = '#PAGE#'


class CorrespondencePage(models.Model):
    """ This class defines a page used for in sponsorship correspondence"""

    _name = 'correspondence.page'

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
