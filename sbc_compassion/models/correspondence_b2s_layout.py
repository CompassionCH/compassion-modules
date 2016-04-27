# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models


class CorrespondenceB2SLayout(models.Model):
    """ This class defines a template used for Supporter Letters and holds
    all information relative to position of metadata in the Template, like for
    instance where the QR Code is supposed to be, where the language
    checkboxes will be found, where the pattern will be, etc...

    Template images should be in 300 DPI
    """

    _name = 'correspondence.b2s.layout'
    _description = 'Child letter layout'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    page_1_box_ids = fields.Many2many(
        'correspondence.translation.box', 'correspondence_b2s_page1_layouts')
    page_2_box_ids = fields.Many2many(
        'correspondence.translation.box', 'correspondence_b2s_page2_layouts')
    additional_page_box_id = fields.Many2one('correspondence.translation.box')
