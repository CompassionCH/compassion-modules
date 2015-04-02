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


class project_project(orm.Model):
    _inherit = "project.project"

    _columns = {
        'project_type': fields.selection([
            ('event', _("Event")),
            ('marketing', _("Marketing campaign"))], _('Type'))
    }

    def on_change_type(self, cr, uid, ids, project_type, context=None):
        """ Set the parent analytic account. """
        res = dict()
        analytic_obj = self.pool.get('account.analytic.account')
        if project_type == 'marketing':
            parent_id = analytic_obj.search(
                cr, uid, [('name', '=', 'Campaign')],
                context={'lang': 'en_US'})
        elif project_type == 'event':
            parent_id = analytic_obj.search(
                cr, uid, [('name', '=', 'Events')],
                context={'lang': 'en_US'})
        res['value'] = {'parent_id': parent_id[0] if parent_id else False}
        return res

    def create(self, cr, uid, vals, context=None):
        type = vals.get('project_type')
        id = super(project_project, self).create(cr, uid, vals, context)
        project = self.browse(cr, uid, id, context)
        analytic_vals = {
            'use_timesheets': True,
            'manager_id': project.user_id.id}
        # if project.project_type: TODO : See if needed
        # analytic_vals['name'] = 'Project/' + project.name
        project.analytic_account_id.write(analytic_vals)
        if type == 'marketing':
            # Create an origin for contracts
            self.pool.get('recurring.contract.origin').create(
                cr, uid, {
                    'type': 'marketing',
                    'partner_id': project.partner_id.id,
                    'analytic_id': project.analytic_account_id.id,
                }, context)
        return id

    def write(self, cr, uid, ids, vals, context=None):
        """ Push the changes to linked events and to analytic account. """
        super(project_project, self).write(cr, uid, ids, vals, context)
        if 'project_type' in vals and not context.get('from_event'):
            raise orm.except_orm(
                _("Type cannot be changed"),
                _("You cannot change the type of the project."))
        if 'user_id' in vals:
            for project in self.browse(cr, uid, ids, context):
                project.analytic_account_id.write({
                    'manager_id': vals['user_id']
                })
        return True

    def unlink(self, cr, uid, ids, context=None):
        """ Unlink analytic account if empty. """
        account_ids = list()
        for project in self.browse(cr, uid, ids, context):
            account = project.analytic_account_id
            if not account.child_ids and not account.line_ids:
                account_ids.append(account.id)
        res = super(project_project, self).unlink(cr, uid, ids, context)
        self.pool.get('account.analytic.account').unlink(cr, uid, account_ids,
                                                         context)
        return res
