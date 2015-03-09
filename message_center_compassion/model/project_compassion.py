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


class compassion_project(orm.Model):
    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. We track if a sponsorship suspension
        is extended. """
        project_id = args.get('object_id')
        project = self.browse(cr, uid, project_id, context)
        was_fund_suspended = (project.suspension == 'fund-suspended')
        self.update_informations(cr, uid, project_id, context)
        project = self.browse(cr, uid, project_id, context)
        if was_fund_suspended and project.suspension == 'fund-suspended':
            # The update was probably sent in order to update the situation
            # of the suspension. We mark the project as so, so that someone
            # can verify the comments of the project and decide to extend
            # or not the suspension of the sponsorships.
            contract_obj = self.pool.get('recurring.contract')
            contract_ids = contract_obj.search(cr, uid, [
                ('child_code', 'like', project.code),
                ('state', 'in', ('active', 'waiting', 'mandate'))],
                context=context)
            contract_obj.write(cr, uid, contract_ids, {
                'gmc_state': 'suspension-extension'}, context)

        return True

    def _get_suspension_state(self, cr, uid, ids, field_name, args,
                              context=None):
        """ Mark sponsorships as reactivated if the project was reactivated.
        """
        contract_obj = self.pool.get('recurring.contract')
        res = super(compassion_project, self)._get_suspension_state(
            cr, uid, ids, field_name, args, context)

        for project in self.browse(cr, uid, ids, context):
            if project.status == 'A' and not res[project.id] and \
                    project.suspension == 'fund-suspended':
                # Project is activated
                contract_ids = contract_obj.search(cr, uid, [
                    ('child_code', 'like', project.code),
                    ('state', 'in', ('active', 'waiting', 'mandate'))],
                    context=context)
                contract_obj.write(cr, uid, contract_ids, {
                    'gmc_state': 'reactivation'}, context)

        return res

    # Redefine suspension field in order to call the inherited function
    _columns = {
        'suspension': fields.function(
            _get_suspension_state, type='selection', selection=[
                ('suspended', _('Suspended')),
                ('fund-suspended', _('Suspended & fund retained'))],
            string=_('Suspension'),
            store={'compassion.project':
                   (lambda self, cr, uid, ids, c=None:
                    ids, ['disburse_funds', 'disburse_gifts',
                          'disburse_unsponsored_funds',
                          'new_sponsorships_allowed',
                          'additional_quota_allowed'], 20)},
            track_visibility='onchange'),
    }
