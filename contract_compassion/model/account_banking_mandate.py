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
        super(account_mandate, self).validate(cr, uid, ids, context)
        self._trigger_contracts(
            cr, uid, ids, 'mandate', 'mandate_validated', context)
        return True

    def cancel(self, cr, uid, ids, context=None):
        """Set back contracts in waiting mandate state."""
        super(account_mandate, self).cancel(cr, uid, ids, context)
        self._trigger_contracts(
            cr, uid, ids, 'active', 'will_pay_by_lsv_dd', context)
        return True

    def _trigger_contracts(self, cr, uid, ids, state, transition,
                           context=None):
        """ Fires a given transition on contracts in selected state. """
        con_ids = set()
        con_obj = self.pool.get('recurring.contract')
        for mandate in self.browse(cr, uid, ids, context):
            con_ids |= set(con_obj.search(
                cr, uid, [('partner_id', '=', mandate.partner_id.id),
                          ('state', '=', state)],
                context=context))
        wf_service = netsvc.LocalService('workflow')
        for con_id in con_ids:
            wf_service.trg_validate(
                uid, 'recurring.contract', con_id, transition, cr)
