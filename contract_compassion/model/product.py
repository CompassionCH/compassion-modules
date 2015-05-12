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

    def _get_categ_name(self, cr, uid, ids, name, args, context=None):
        return {p.id: p.product_tmpl_id.categ_id.name for p in
                self.browse(cr, uid, ids, {'lang': 'en_US'})}

    _columns = {
        'gp_fund_id': fields.integer("GP Fund id", size=4),
        'categ_name': fields.function(
            _get_categ_name,
            type="char", string=_('Product category'),
            store=True)
    }
