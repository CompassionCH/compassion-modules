# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models


class ResCountry(models.Model):

    """ This class upgrade the countries to add spoken languages
    to match Compassion needs.
    """

    _inherit = 'compassion.country'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    spoken_langs_ids = fields.Many2many('res.lang.compassion')
