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

from openerp.osv import orm, fields


class account_invoice_line(orm.Model):
    """ We add a field for gift instructions. """
    _inherit = "account.invoice.line"

    def _get_gift_info(self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        for inv_line in self.browse(cr, uid, ids, context):
            if field_name == 'need_key':
                need_key = inv_line.contract_id.child_code
                if inv_line.product_id.gmc_name == 'ProjectGift':
                    need_key = need_key[:5]
                res[inv_line.id] = need_key
        return res

    def _get_instructions(self, cr, uid, ids, field, args, context=None):
        res = dict()
        ctx = context.copy()
        for inv_line in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            ctx['lang'] = inv_line.partner_id.lang
            product = self.pool.get('product.product').browse(
                cr, uid, inv_line.product_id.id, ctx)
            if inv_line.product_id.name == inv_line.name or \
                    product.name == inv_line.name:
                res[inv_line.id] = ''
            else:
                res[inv_line.id] = inv_line.name
        return res

    _columns = {
        'gift_instructions': fields.function(
            _get_instructions, type='char'),
        'need_key': fields.function(_get_gift_info, type='char')
    }
