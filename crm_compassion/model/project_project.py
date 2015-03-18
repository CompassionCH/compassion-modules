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
        res = {}
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
        if project.project_type:
            analytic_vals['name'] = 'Project-' + project.name
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
        if 'project_type' in vals:
            raise orm.except_orm(
                _("Type cannot be changed"),
                _("You cannot change the type of the project."))
        event_vals = dict()
        if 'user_id' in vals:
            event_vals['user_id'] = vals['user_id']
            for project in self.browse(cr, uid, ids, context):
                project.analytic_account_id.write({
                    'manager_id': vals['user_id']
                })
        if 'name' in vals:
            event_vals['name'] = vals['name']
        if event_vals and not context.get('from_event'):
            event_obj = self.pool.get('crm.event.compassion')
            event_ids = event_obj.search(
                cr, uid, [('project_id', 'in', ids)], context=context)
            if event_ids:
                event_obj.write(cr, uid, event_ids, event_vals, context)
        return True
