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
    #                                 FIELDS                                 #
    ##########################################################################

    name = fields.Char(size=128, store=True)
    code_iso = fields.Char(size=128, store=True)
