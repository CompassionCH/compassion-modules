# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, _


class CorrespondencePage(models.Model):
    """ This class defines a page used for in sponsorship correspondence"""

    _name = 'sponsorship.correspondence.page'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    sponsorship_correspondence_id = fields.Many2one(
        'sponsorship.correspondence', ondelete='cascade', required=True)

    original_page_url = fields.Char()
    final_page_url = fields.Char()
    original_text = fields.Text()
    english_translated_text = fields.Text()
    translated_text = fields.Text()

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
