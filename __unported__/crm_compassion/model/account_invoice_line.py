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

    def _get_invoice_line_from_contract(contract_obj, cr, uid, ids,
                                        context=None):
        res = list()
        for contract in contract_obj.browse(cr, uid, ids, context):
            res.extend([l.id for l in contract.invoice_line_ids])
        return res

    _columns = {
        'user_id': fields.related(
            'contract_id', 'user_id', type='many2one', relation='res.partner',
            string=_('Ambassador'), store={
                'recurring.contract': (
                    _get_invoice_line_from_contract,
                    ['user_id'],
                    10)}),
    }
