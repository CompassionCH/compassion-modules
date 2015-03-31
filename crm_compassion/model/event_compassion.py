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

from datetime import datetime


class event_compassion(orm.Model):
    """A Compassion event. """
    _name = 'crm.event.compassion'
    _description = 'Compassion event'
    _order = 'start_date desc'

    _inherit = ['mail.thread']

    def _get_analytic_lines(self, cr, uid, ids, field_name, arg, context=None):
        res = dict()
        line_obj = self.pool.get('account.analytic.line')
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            if event.analytic_id:
                line_ids = line_obj.search(
                    cr, uid, [
                        ('account_id', '=', event.analytic_id.id)],
                    context=context)
                res[event.id] = line_ids
            else:
                res[event.id] = False

        return res

    def _get_won_sponsorships(self, cr, uid, ids, field_name, arg,
                              context=None):
        res = dict()
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            contract_ids = [contract.id for contract in event.contract_ids
                            if contract.state in ('active', 'terminated')]
            res[event.id] = len(contract_ids)
        return res

    def _get_event_from_contract(contract_obj, cr, uid, ids, context=None):
        res = []
        for contract in contract_obj.browse(cr, uid, ids, context):
            if contract.state == 'active' and contract.origin_id.event_id:
                res.append(contract.origin_id.event_id.id)
        return res

    def _get_year(self, cr, uid, ids, field_name, arg, context=None):
        res = dict()
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            res[event.id] = event.start_date[:4]
        return res

    def _get_full_name(self, cr, uid, ids, field_name, arg, context=None):
        return {e.id: e.type.title() + ' ' + e.name + ' ' + e.year
                for e in self.browse(cr, uid, ids, context)}

    def get_event_types(self, cr, uid, context=None):
        return [
            ('stand', _("Stand")),
            ('concert', _("Concert")),
            ('presentation', _("Presentation")),
            ('meeting', _("Meeting")),
            ('sport', _("Sport event"))]

    _columns = {
        'name': fields.char(_("Name"), size=128, required=True,
                            track_visibility='onchange'),
        'full_name': fields.function(_get_full_name, type='char',
                                     string='Full name'),
        'type': fields.selection(get_event_types, _("Type"), required=True,
                                 track_visibility='onchange'),
        'start_date': fields.datetime(_("Start date"), required=True),
        'year': fields.function(_get_year, type='char', string='Year',
                                store=True),
        'end_date': fields.datetime(_("End date")),
        'partner_id': fields.many2one('res.partner', _("Customer"),
                                      track_visibility='onchange'),
        'zip_id': fields.many2one('res.better.zip', 'Address'),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one('res.country.state', 'State'),
        'zip': fields.char('ZIP', size=24),
        'country_id': fields.many2one('res.country', 'Country'),
        'user_id': fields.many2one('res.users', _("Ambassador"),
                                   track_visibility='onchange'),
        'staff_ids': fields.many2many(
            'res.partner', 'partners_to_staff_event', 'event_id',
            'partner_id', _("Staff")),
        'description': fields.text('Description'),
        'analytic_id': fields.many2one('account.analytic.account',
                                       'Analytic Account'),
        'origin_id': fields.many2one('recurring.contract.origin', 'Origin'),
        'contract_ids': fields.related(
            'origin_id', 'contract_ids', type="one2many",
            relation="recurring.contract", readonly=True),
        'analytic_line_ids': fields.function(
            _get_analytic_lines, type="one2many",
            relation="account.analytic.line", readonly=True),
        'planned_sponsorships': fields.integer(_("Expected sponsorships"),
                                               track_visibility='onchange'),
        'lead_id': fields.many2one('crm.lead', _('Opportunity'),
                                   track_visibility='onchange'),
        'won_sponsorships': fields.function(
            _get_won_sponsorships, type="integer",
            string=_("Won sponsorships"), store={
                'recurring.contract': (
                    _get_event_from_contract,
                    ['state'],
                    10),
                'crm.event.compassion': (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['contract_ids', 'description'],
                    10)
            }),
        'project_id': fields.many2one('project.project', _("Project")),
        'project_name': fields.related(
            'project_id', 'name', type='char', string=_('Project name'),
            store=True, track_visibility='onchange'),
    }

    def create(self, cr, uid, vals, context=None):
        """ When an event is created:
        - Format the name to remove year of it,
        - Retrieve a corresponding Project (for tasks) or create a new one,
        - Create a child analytic_account to the project's one,
        - Create an origin for sponsorships.
        """
        if context is None:
            context = dict()
        context['from_event'] = True
        # Avoid putting twice the date in linked objects name
        event_year = vals.get('start_date',
                              datetime.today().strftime('%Y'))[:4]
        event_name = vals.get('name', '0000')
        if event_name[-4:] == event_year:
            vals['name'] = event_name[:-4]
        elif event_name[-2:] == event_year[-2:]:
            vals['name'] = event_name[:-2]

        new_id = super(event_compassion, self).create(cr, uid, vals, context)
        event = self.browse(cr, uid, new_id, context)

        # Create Project, Analytic account and Origin linked to this event
        project_obj = self.pool.get('project.project')
        project_id = event.project_id and event.project_id.id or \
            event.lead_id and event.lead_id.event_ids and \
            event.lead_id.event_ids[-1].project_id.id or \
            project_obj.create(
                cr, uid, self._get_project_vals(
                    cr, uid, event, create=True, context=context), context)
        parent_analytic_id = project_obj.browse(
            cr, uid, project_id, context).analytic_account_id.id
        analytic_id = self.pool.get('account.analytic.account').create(
            cr, uid, self._get_analytic_vals(
                cr, uid, event, parent_analytic_id, context),
            context)
        origin_id = self.pool.get('recurring.contract.origin').create(
            cr, uid, self._get_origin_vals(
                cr, uid, event, analytic_id, context), context)
        super(event_compassion, self).write(cr, uid, event.id, {
            'origin_id': origin_id,
            'analytic_id': analytic_id,
            'project_id': project_id,
        }, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """ Push values to linked objects. """
        if 'lead_id' in vals:
            # Move events to another project related to the opporunity
            other_events_ids = self.search(cr, uid, [(
                'lead_id', '=', vals['lead_id'])], context=context)
            if other_events_ids:
                # Attach event to same project than those related to this
                # opportunity.
                new_project = self.browse(
                    cr, uid, other_events_ids[0], context).project_id
                vals['project_id'] = new_project.id

            else:
                # Update project name
                proj_name = self.pool.get('crm.lead').browse(
                    cr, uid, vals['lead_id'], context).name
                for event in self.browse(cr, uid, ids, context):
                    event.project_id.write({'name': proj_name})

        project_obj = self.pool.get('project.project')
        to_remove_project_ids = list()
        if 'project_id' in vals:
            task_type_obj = self.pool.get('project.task.type')
            for event in self.browse(cr, uid, ids, context):
                # Add project stage for this event.
                task_type_id = task_type_obj.search(
                    cr, uid, [('description', 'like', str(event.id))],
                    context=context)
                if task_type_id:
                    project_obj.write(cr, uid, vals['project_id'], {
                        'type_ids': [(4, task_type_id[0])]}, context)
                # Remove old project if empty
                other_events_ids = self.search(cr, uid, [
                    ('project_id', '=', event.project_id.id),
                    ('id', '!=', event.id)], context=context)
                if not other_events_ids:
                    to_remove_project_ids.append(event.project_id.id)

        super(event_compassion, self).write(cr, uid, ids, vals, context)

        if context is None:
            context = dict()
        context['from_event'] = True
        for event in self.browse(cr, uid, ids, context):
            event.project_id.write(self._get_project_vals(cr, uid, event,
                                                          context=context))
            event.analytic_id.write(self._get_analytic_vals(
                cr, uid, event, event.project_id.analytic_account_id.id,
                context))
            self.pool.get('recurring.contract.origin').write(
                cr, 1, event.origin_id.id, {
                    'name': event.full_name}, context)

        if to_remove_project_ids:
            project_obj.unlink(cr, uid, to_remove_project_ids, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        """Check that the event is not linked with expenses or won
        sponsorships."""
        for event in self.browse(cr, uid, ids, context):
            if event.contract_ids or event.analytic_line_ids:
                raise orm.except_orm(
                    _('Not authorized action'),
                    _('The event is linked to expenses or sponsorships. '
                      'You cannot delete it.'))
            else:
                if len(event.project_id.event_ids) <= 1:
                    event.project_id.unlink()
                event.analytic_id.unlink()
                event.origin_id.unlink()
        return super(event_compassion, self).unlink(cr, uid, ids, context)

    def create_from_gp(self, cr, uid, vals, context=None):
        """ DEPRECATED """
        if context is None:
            context = dict()
        # Don't create project tasks for an old Event imported from GP.
        context['use_tasks'] = False
        return self.create(cr, uid, vals, context)

    def _get_project_vals(self, cr, uid, event, create=False, context=None):
        """ Creates a new project based on the event.
        """
        res = dict()
        if create:
            members = self.pool.get('res.users').search(
                cr, uid,
                [('partner_id', 'in', [p.id for p in event.staff_ids])],
                context=context)
            parent_id = self.pool.get('account.analytic.account').search(
                cr, uid, [('name', '=', 'Events')],
                context={'lang': 'en_US'})[0]
            task_type_id = self._create_task_type(cr, uid, event, context)
            res.update({
                'name': event.project_name or event.lead_id
                and event.lead_id.name or event.name + ' ' + event.year,
                'use_tasks': True,
                'parent_id': parent_id,
                'project_type': 'event',
                'user_id': event.user_id.id,
                'partner_id': event.partner_id.id,
                'members': [(6, 0, members)],   # many2many field
                'date_start': event.start_date,
                'date': event.end_date,
                'state': 'open',
                'type_ids': [(6, 0, [task_type_id])],
            })
        else:
            res['name'] = event.project_name
            # Update task type of project
            task_type_obj = self.pool.get('project.task.type')
            task_type_id = task_type_obj.search(cr, uid, [
                ('description', 'like', str(event.id))], context=context)
            project_task_types = [t.id for t in event.project_id.type_ids]
            if task_type_id and task_type_id[0] in project_task_types:
                res['type_ids'] = [(1, task_type_id[0], {
                    'name': event.full_name})]
            else:
                # Attach a new task type
                if task_type_id:
                    task_type_id = task_type_id[0]
                else:
                    task_type_id = self._create_task_type(cr, uid, event,
                                                          context)
                res['type_ids'] = [(4, task_type_id)]

        return res

    def _create_task_type(self, cr, uid, event, context=None):
        """ Create a new project task type """
        task_type_obj = self.pool.get('project.task.type')
        task_type_id = task_type_obj.create(cr, uid, {
            'name': event.full_name,
            'state': 'open',
            'description': 'Task type generated for event ID ' + str(
                event.id),
            'sequence': 1}, context)
        return task_type_id

    def _get_analytic_vals(self, cr, uid, event, parent_id, context=None):
        return {
            'name': event.name,
            'type': 'event',
            'event_type': event.type,
            'date_start': event.start_date,
            'date': event.end_date,
            'parent_id': parent_id,
            'use_timesheets': True,
            'partner_id': event.partner_id.id,
            'manager_id': event.user_id.id,
            'user_id': event.user_id.id,
        }

    def _get_origin_vals(self, cr, uid, event, analytic_id, context=None):
        return {
            'type': 'event',
            'event_id': event.id,
            'analytic_id': analytic_id,
        }

    def show_tasks(self, cr, uid, ids, context=None):
        event = self.browse(cr, uid, ids[0], context)
        project_id = event.project_id.id
        return {
            'name': 'Project Tasks',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form,calendar,gantt,graph',
            'view_type': 'form',
            'res_model': 'project.task',
            'src_model': 'crm.event.compassion',
            'context': {
                'search_default_project_id': [project_id],
                'default_project_id': project_id,
                'active_test': False},
            'search_view_id': self.pool.get(
                'ir.model.data'
            ).get_object_reference(cr, uid, 'project',
                                   'view_task_search_form')[1]
        }
