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

from openerp.osv import orm


class invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    def _get_gift_info(self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        for inv_line in self.browse(cr, uid, ids, context):
            if field_name == 'need_key':
                need_key = inv_line.contract_id.child_code
                if inv_line.product_id.gmc_name == 'ProjectGift':
                    need_key = need_key[:5]
                res[inv_line.id] = need_key
        return res
    
    def get_gift_details(self, cr, uid, line_id, context=None):
        inv_line = self.browse(cr, uid, line_id, context)
        need_key = inv_line.contract_id.child_code
        if inv_line.product_id.gmc_name == 'ProjectGift':
            need_key = need_key[:5]
        res = {
            'ConstituentId': inv_line.partner_id.id,
            'NeedKey': inv_line.contract_id.child_code,
            'GiftType': inv_line.product_id.gmc_name,
            'GiftAmount': inv_line.price_subtotal,
            'GiftInstructions': inv_line.name,
            'TransactionDate': inv_line.invoice_id.date_invoice
        }
        return res
        
    _columns = {
        'need_key': fields.function(_get_gift_info, type='char')
    }
