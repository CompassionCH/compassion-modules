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
    _name = "crm.event.compassion"
    _description = "Compassion event"

    _inherit = ['mail.thread']

    def _get_analytic_lines(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
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
        res = {}
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

    _columns = {
        'name': fields.char(_("Name"), size=128, required=True),
        'type': fields.selection([
            ('stand', _("Stand")),
            ('concert', _("Concert")),
            ('presentation', _("Presentation")),
            ('meeting', _("Meeting")),
            ('sport', _("Sport event"))], _("Type"), required=True),
        'start_date': fields.datetime(_("Start date"), required=True),
        'year': fields.function(_get_year, type='char', string='Year',
                                store=True),
        'end_date': fields.datetime(_("End date")),
        'partner_id': fields.many2one('res.partner', _("Customer")),
        'zip_id': fields.many2one('res.better.zip', 'Address'),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one('res.country.state', 'State'),
        'zip': fields.char('ZIP', size=24),
        'country_id': fields.many2one('res.country', 'Country'),
        'user_id': fields.many2one('res.users', _("Responsible"),
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
        'planned_sponsorships': fields.integer(_("Expected sponsorships")),
        'lead_id': fields.many2one('crm.lead', _('Opportunity'),
                                   readonly=True),
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
        'project_id': fields.many2one('project.project', _("Project"))
    }

    def create(self, cr, uid, vals, context=None):
        """ When an event is created:
        - link it to the originating Opportunity,
        - create a project and link to its analytic account,
        - create an origin for sponsorships.
        """
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
        project_id = event.project_id and event.project_id.id or \
            self.pool.get('project.project').create(
                cr, uid, self._get_project_vals(cr, uid, event, context),
                context)
        analytic_id = self.pool.get('account.analytic.account').create(
            cr, uid, self._get_analytic_vals(cr, uid, event, context), context)
        origin_id = self.pool.get('recurring.contract.origin').create(
            cr, uid, self._get_origin_vals(
                cr, uid, event, analytic_id, context), context)
        event.write({
            'origin_id': origin_id,
            'analytic_id': analytic_id,
            'project_id': project_id,
        })
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """ Push values to linked objects. """ TODOOOOOOOOOOOOOOO
        super(event_compassion, self).write(cr, uid, ids, vals, context)
        project_vals = dict()
        origin_vals = dict()
        analytic_vals = dict()
        ctx = context.copy()
        ctx['from_event'] = True
        if 'type' in vals:
            project_vals.update({'project_type': vals['type']})
        if 'user_id' in vals:
            project_vals.update({'user_id': vals['user_id']})
        if 'partner_id' in vals:
            project_vals.update({'partner_id': vals['partner_id']})
        if 'name' in vals:
            project_vals.update({'name': vals['name']})
        if project_vals:
            for event in self.browse(cr, uid, ids, context):
                if 'type' in vals:
                    # Change parent of analytic account
                    project_vals.update({
                        'parent_id': self._find_parent_analytic(
                            cr, uid, vals['type'], event.year, context)})
                event.project_id.write(project_vals, context=ctx)

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
                if event.project_id:
                    event.project_id.unlink()
                if event.analytic_id:
                    event.analytic_id.unlink()
        return super(event_compassion, self).unlink(cr, uid, ids, context)

    def create_from_gp(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        # Don't create project tasks for an old Event imported from GP.
        context['use_tasks'] = False
        return self.create(cr, uid, vals, context)

    def _get_project_vals(self, cr, uid, event, context=None):
        """ Creates a new project based on the event.
        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        ctx['from_event'] = True
        members = self.pool.get('res.users').search(
            cr, uid,
            [('partner_id', 'in', [p.id for p in event.staff_ids])],
            context=ctx)
        project_obj = self.pool.get('project.project')
        return {
            'name': event.name,
            'use_tasks': ctx.get('use_tasks', True),
            'user_id': event.user_id.id,
            'partner_id': event.partner_id.id,
            'members': [(6, 0, members)],   # many2many field
            'date_start': event.start_date,
            'date': event.end_date,
            'parent_id': self._find_parent_analytic(cr, uid, event.type,
                                                    event.year, ctx),
            'project_type': event.type,
            'state': 'open' if ctx.get('use_tasks', True) else 'close',
        }

    def _get_analytic_vals(self, cr, uid, event, parent_id, context=None):
        return {
            # TODO : see if naming scheme is good
            'name': event.year + '/' + event.type + '/' + event.name,
            'type': 'normal',
            'parent_id': parent_id,
            'use_timesheets': True,
            'partner_id': event.partner_id.id,
            'manager_id': event.user_id.id,
            'user_id': event.user_id.id,
        }

    def _get_origin_vals(self, cr, uid, event, analytic_id, context=None):
        return {
            'name': event.name + ' ' + event_year,
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
