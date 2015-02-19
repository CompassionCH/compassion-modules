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

from openerp.osv import orm


class project_compassion(orm.Model):
    _inherit = 'compassion.project'

    def suspend_funds(self, cr, uid, project_id, start, context=None):
        """ When a project is suspended, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        We also remove the children on internet.
        """
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, [
            ('child_code', 'like', project.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))],
            context=context)
        # For now, suspend the contract for 3 months
        contract_obj.suspend_contract(cr, uid, contract_ids, start, 3,
                                      context)
        return True
