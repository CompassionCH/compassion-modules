# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'type': fields.selection([
            ('S', _('Sponsorship')),
            ('B', _('Both')),
            ('G', _('Gift')),
            ('O', _('Others'))], _('Type'), select=True,
            readonly=True)
    }
