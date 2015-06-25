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

    def suspend_funds(self, cr, uid, project_id, context=None):
        """ When a project is suspended, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        We also remove the children on internet.
        """
        res = super(project_compassion, self).suspend_funds(
            cr, uid, project_id, context)
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, [
            ('child_code', 'like', project.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))],
            context=context)
        res = res and contract_obj.suspend_contract(
            cr, uid, contract_ids, context)
        return res

    def _reactivate_project(self, cr, uid, project_id, context=None):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        super(project_compassion, self)._reactivate_project(
            cr, uid, project_id, context)
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(cr, uid, [
            ('child_code', 'like', project.code),
            ('state', 'in', ('active', 'waiting', 'mandate'))],
            context=context)
        contract_obj.reactivate_contract(cr, uid, contract_ids, context)
