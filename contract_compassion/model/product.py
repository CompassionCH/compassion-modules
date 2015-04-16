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
import pdb

class product(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'type': fields.selection([
            ('S', _('Sponsorship')),
            ('B', _('Both')),
            ('O', _('Others'))], _('Type'), select=True,
            readonly=True)
    }
    def field_view_get(cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        pdb.set_trace()
    def get_type(self, cr, uid, ids, type):
        pdb.set_trace()
    # def onchange_type(self, cr, uid, ids, type, context=None):
        # product_obj = self.pool.get('product.product')
        # product_ids = product_obj.search(cr,uid, [('type','=',type)])
        # pdb.set_trace()
        # return {'domain':{'product_id':[('id','in',product_ids)]}}
    # def name_search(cr, user, name='product_id', args=None, operator='ilike', context=None, limit=100):
        # pdb.set_trace()