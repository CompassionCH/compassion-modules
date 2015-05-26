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


class end_sponsorship_wizard(orm.TransientModel):
    _inherit = 'end.contract.wizard'

    def _get_exit_reason(self, cr, uid, context=None):
        return self.pool.get('compassion.child').get_gp_exit_reasons(cr, uid)

    _columns = {
        'gp_exit_reason': fields.selection(
            _get_exit_reason, string=_('Exit reason')),
    }

    def end_contract(self, cr, uid, ids, context=None):
        res = super(end_sponsorship_wizard, self).end_contract(
            cr, uid, ids, context)
        wizard = self.browse(cr, uid, ids[0], context)

        if wizard.child_id and wizard.contract_id.type == 'S':
            # If sponsor moves, the child may be transferred
            if wizard.do_transfer:
                wizard.child_id.write({
                    'state': 'F',
                    'transfer_country_id': wizard.transfer_country_id.id,
                    'exit_date': wizard.end_date})

            # If child has departed, write exit_details
            elif wizard.end_reason == '1':
                wizard.child_id.write({
                    'state': 'F',
                    'gp_exit_reason': wizard.gp_exit_reason,
                    'exit_date': wizard.end_date})
        return res
