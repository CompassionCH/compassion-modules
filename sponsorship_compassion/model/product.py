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

GIFT_TYPES = ['Birthday Gift', 'General Gift',
              'Family Gift', 'Project Gift', 'Graduation Gift']


class product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'gp_fund_id': fields.integer("GP Fund id", size=4),
    }
