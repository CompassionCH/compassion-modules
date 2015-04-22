# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm


class compassion_project(orm.Model):
    """ Update Contracts Project Workflow when Suspension status
        is changed.
    """
    _inherit = 'compassion.project'

    def suspend_funds(self, cr, uid, project_id, context=None,
                      date_start=None, date_end=None):
        super(compassion_project, self).suspend_funds(
            cr, uid, project_id, context, date_start, date_end)

        return self._transition_contracts(
            cr, uid, project_id, 'project_suspended', context)

    def _reactivate_project(self, cr, uid, project_id, context=None):
        super(compassion_project, self)._reactivate_project(
            cr, uid, project_id, context)

        return self._transition_contracts(
            cr, uid, project_id, 'project_reactivation', context)

    def _suspend_extension(self, cr, uid, project_id, context=None):
        super(compassion_project, self)._suspend_extension(
            cr, uid, project_id, context)

        return self._transition_contracts(
            cr, uid, project_id, 'project_suspension_extension', context)

    def _transition_contracts(self, cr, uid, project_id, transition,
                              context=None):
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(
            cr, uid, [('project_id', '=', project_id)], context=context)
        return contract_obj.trg_validate(cr, uid, contract_ids, transition,
                                         context)
