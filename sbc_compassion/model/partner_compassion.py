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

from openerp import fields, models


class ResPartner(models.Model):

    """ This class upgrade the partners to match Compassion needs.
    """

    _inherit = 'res.partner'

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    spoken_lang = fields.Many2many('res.lang.compassion')
