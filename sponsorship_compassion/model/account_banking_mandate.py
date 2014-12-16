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
from openerp import netsvc


class account_mandate(orm.Model):
    _inherit = 'account.banking.mandate'

    def validate(self, cr, uid, ids, context=None):
        """Validate LSV/DD Contracts when mandate is validated."""
        if super(account_mandate, self).validate(cr, uid, ids, context):
            wf_service = netsvc.LocalService('workflow')
            for mandate in self.browse(cr, uid, ids, context):
                contract_ids = self.pool.get('recurring.contract').search(
                    cr, uid, [('partner_id', '=', mandate.partner_id.id),
                              ('state', '=', 'mandate')], context=context)
                for con_id in contract_ids:
                    wf_service.trg_validate(
                        uid, 'recurring.contract', con_id,
                        'mandate_validated', cr)
        return True
