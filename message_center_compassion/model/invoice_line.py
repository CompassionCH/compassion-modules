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


class invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    def get_gift_details(self, cr, uid, line_id, context=None):
        inv_line = self.browse(cr, uid, line_id, context)
        res = {
            'ConstituentId': inv_line.partner_id.id,
            'NeedKey': inv_line.contract_id.child_code,
            'GiftType': inv_line.product_id.gmc_name,
            'GiftAmount': inv_line.price_subtotal,
            'GiftInstructions': inv_line.name,
            'TransactionDate': inv_line.invoice_id.date_invoice
        }
        return res
