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


class ResLang(models.Model):

    """ This class add spoken languages to match Compassion needs.
    """

    _name = 'res.lang.compassion'

    ##########################################################################
    #                        NEW LANG FIELDS                              #
    ##########################################################################

    name = fields.Char(size=128, store=True)
    ISO_code = fields.Char(size=128, store=True)
