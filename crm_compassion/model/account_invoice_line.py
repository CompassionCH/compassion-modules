# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_invoice_line(orm.Model):
    """ Add salespersons to invoice_lines. """
    _inherit = "account.invoice.line"

    _columns = {
        'user_id': fields.many2one(
            'res.partner', string=_('Ambassador'))
    }

    def on_change_contract_id(self, cr, uid, ids, contract_id, context=None):
        """ Push Ambassador to invoice line. """
        res = dict()
        user = False
        if contract_id:
            contract = self.pool.get('recurring.contract').browse(
                cr, uid, contract_id, context)
            if contract.user_id:
                user = contract.user_id.id

        res['value'] = {'user_id': user}
        return res


class generate_gift_wizard(orm.TransientModel):
    """ Push salespersons to generated invoices """
    _inherit = 'generate.gift.wizard'

    def _setup_invoice_line(self, cr, uid, invoice_id, wizard,
                            contract, context=None):
        invl_data = super(generate_gift_wizard, self)._setup_invoice_line(
            cr, uid, invoice_id, wizard, contract, context)
        if contract.user_id:
            invl_data['user_id'] = contract.user_id.id
        return invl_data
