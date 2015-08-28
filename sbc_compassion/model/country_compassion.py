# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, fields, models, _

class ResCountry(models.Model):

    """ This class upgrade the partners to match Compassion needs.
    """

    _inherit = 'compassion.country'

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    spoken_langs = fields.Many2many('res.lang.compassion')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################


    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
