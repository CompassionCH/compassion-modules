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


class ResLang(models.Model):

    """ This class upgrade the partners to match Compassion needs.
    """

    _name = 'res.lang.compassion'

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################

    name = fields.Char(size=128, store=True)
    ISO_code = fields.Char(size=128, store=True)
