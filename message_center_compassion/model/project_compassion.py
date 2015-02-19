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


class compassion_project(orm.Model):
    """ Add update method. """
    _inherit = 'compassion.project'

    def update(self, cr, uid, args, context=None):
        """ When we receive a notification that a project has been updated,
        we fetch the last informations. """
        self.update_informations(cr, uid, args.get('object_id'), context)
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
