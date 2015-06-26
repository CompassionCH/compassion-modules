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


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    def unlink(self, cr, uid, ids, context=None):
        """ Override unlink to recompute expense/income of events. """
        event_obj = self.pool.get('crm.event.compassion')
        line_obj = self.pool.get('account.analytic.line')
        analytic_line_ids = line_obj.search(
            cr, uid, [('move_id', 'in', ids)], context=context)
        account_ids = [l.account_id.id for l in line_obj.browse(
            cr, uid, analytic_line_ids, context)]
        event_ids = event_obj.search(cr, uid, [
            ('analytic_id', 'in', account_ids)], context=context)
        res = super(account_move_line, self).unlink(cr, uid, ids, context)
        event_obj._store_set_values(cr, uid, event_ids, [
            'total_income', 'total_expense', 'balance'], context)
        return res


class event_compassion(orm.Model):
    """A Compassion event. """
    _name = 'crm.event.compassion'
    _description = 'Compassion event'
    _order = 'start_date desc'

    _inherit = ['mail.thread']

    def _get_analytic_lines(self, cr, uid, ids, field_names, arg,
                            context=None):
        res = dict()
        field_res = dict()
        line_obj = self.pool.get('account.analytic.line')
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            if event.analytic_id:
                expense_ids = line_obj.search(
                    cr, uid, [
                        ('account_id', '=', event.analytic_id.id),
                        ('amount', '<', '0.0')], context=context)
                income_ids = line_obj.search(
                    cr, uid, [
                        ('account_id', '=', event.analytic_id.id),
                        ('amount', '>', '0.0')], context=context)
                field_res['expense_line_ids'] = expense_ids or False
                field_res['income_line_ids'] = income_ids or False
                field_res['total_expense'] = abs(sum(
                    [l.amount for l in line_obj.browse(cr, uid, expense_ids,
                                                       context)]))
                field_res['total_income'] = sum(
                    [l.amount for l in line_obj.browse(cr, uid, income_ids,
                                                       context)])
                field_res['balance'] = field_res['total_income'] - \
                    field_res['total_expense']
            else:
                field_res['expense_line_ids'] = False
                field_res['income_line_ids'] = False
                field_res['total_expense'] = 0.0
                field_res['total_income'] = 0.0
                field_res['balance'] = 0.0
            res[event.id] = field_res.copy()

        return res

    def _analytic_line_to_events(line_obj, cr, uid, line_ids, context=None):
        self = line_obj.pool.get('crm.event.compassion')
        res = list()
        for line in line_obj.browse(cr, uid, line_ids, context):
            res.extend(self.search(cr, uid, [
                ('analytic_id', '=', line.account_id.id)], context=context))
        return res

    def _get_event_from_origin(origin_obj, cr, uid, ids, context=None):
        self = origin_obj.pool.get('crm.event.compassion')
        return self.search(cr, uid, [(
            'origin_id', 'in', ids)], context=context)

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
        'expense_line_ids': fields.function(
            _get_analytic_lines, type="one2many", multi='analytic_line',
            relation="account.analytic.line", readonly=True),
        'income_line_ids': fields.function(
            _get_analytic_lines, type="one2many",  multi='analytic_line',
            relation="account.analytic.line", readonly=True),
        'total_expense': fields.function(
            _get_analytic_lines, type="float", multi='analytic_line',
            readonly=True, string=_("Total expense"), store={
                'account.analytic.line': (
                    _analytic_line_to_events, ['amount', 'account_id'], 10)
            }),
        'total_income': fields.function(
            _get_analytic_lines, type="float", multi='analytic_line',
            readonly=True, string=_("Total income"), store={
                'account.analytic.line': (
                    _analytic_line_to_events, ['amount', 'account_id'], 20)
            }),
        'balance': fields.function(
            _get_analytic_lines, type="float", multi='analytic_line',
            readonly=True, string=_("Balance"), store={
                'account.analytic.line': (
                    _analytic_line_to_events, ['amount', 'account_id'], 30)
            }),
        'planned_sponsorships': fields.integer(_("Expected sponsorships"),
                                               track_visibility='onchange'),
        'lead_id': fields.many2one('crm.lead', _('Opportunity'),
                                   track_visibility='onchange'),
        'won_sponsorships': fields.related(
            'origin_id', 'won_sponsorships', type="integer",
            string=_("Won sponsorships"), store={
                'recurring.contract.origin': (
                    _get_event_from_origin,
                    ['won_sponsorships'],
                    10)
            }),
        'project_id': fields.many2one('project.project', 'Project'),
        'use_tasks': fields.boolean(_('Use tasks')),
        'parent_id': fields.many2one('account.analytic.account', _('Parent'),
                                     track_visibility='onchange'),
        # This field circumvents problem for passing parent_id in a subview.
        'parent_copy': fields.related(
            'parent_id', type='many2one', relation='account.analytic.account',
            string='Parent copy'),
    }

    def create(self, cr, uid, vals, context=None):
        """ When an event is created:
        - Format the name to remove year of it,
        - Create an analytic_account,
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

        # Create project for the tasks
        project_id = False
        if event.use_tasks:
            project_id = self.pool.get('project.project').create(
                cr, uid, self._get_project_vals(
                    cr, uid, event, context), context)

        # Analytic account and Origin linked to this event
        analytic_id = self.pool.get('account.analytic.account').create(
            cr, uid, self._get_analytic_vals(
                cr, uid, event, context),
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
        super(event_compassion, self).write(cr, uid, ids, vals, context)

        if context is None:
            context = dict()
        ctx = context.copy()
        ctx['from_event'] = True
        for event in self.browse(cr, uid, ids, ctx):
            if 'use_tasks' in vals and event.use_tasks:
                project_id = self.pool.get('project.project').create(
                    cr, uid, self._get_project_vals(
                        cr, uid, event, ctx), ctx)
                event.write({'project_id': project_id})
            elif event.project_id:
                event.project_id.write(self._get_project_vals(
                    cr, uid, event, ctx))
            event.analytic_id.write(self._get_analytic_vals(
                cr, uid, event, ctx))
            if 'name' in vals:
                self.pool.get('recurring.contract.origin').write(
                    # Only administrator has write access to origins.
                    cr, 1, event.origin_id.id, {
                        'name': event.full_name}, ctx)

        return True

    def unlink(self, cr, uid, ids, context=None):
        """Check that the event is not linked with expenses or won
        sponsorships."""
        for event in self.browse(cr, uid, ids, context):
            if event.contract_ids or event.balance:
                raise orm.except_orm(
                    _('Not authorized action'),
                    _('The event is linked to expenses or sponsorships. '
                      'You cannot delete it.'))
            else:
                if event.project_id:
                    event.project_id.unlink()
                if event.analytic_id:
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

    def _get_project_vals(self, cr, uid, event, context=None):
        """ Creates a new project based on the event.
        """
        members = self.pool.get('res.users').search(
            cr, uid,
            [('partner_id', 'in', [p.id for p in event.staff_ids])],
            context=context)
        return {
            'name': event.full_name,
            'use_tasks': True,
            'analytic_account_id': event.analytic_id.id,
            'project_type': event.type,
            'user_id': event.user_id.id,
            'partner_id': event.partner_id.id,
            'members': [(6, 0, members)],   # many2many field
            'date_start': event.start_date,
            'date': event.end_date,
            'state': 'open',
        }

    def _get_analytic_vals(self, cr, uid, event, context=None):
        name = event.name
        parent_id = event.parent_id and event.parent_id.id
        if event.city:
            name += ' ' + event.city
        if not parent_id:
            parent_id = self._find_parent_analytic(
                cr, uid, event.type, event.year, context)
            super(event_compassion, self).write(cr, uid, event.id, {
                'parent_id': parent_id}, context)
        return {
            'name': name,
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

    def _find_parent_analytic(self, cr, uid, event_type, year, context=None):
        analytics_obj = self.pool.get('account.analytic.account')
        categ_id = analytics_obj.search(
            cr, uid, [('name', 'ilike', event_type)], context=context)[0]
        acc_ids = analytics_obj.search(
            cr, uid, [('name', '=', year), ('parent_id', '=', categ_id)],
            context=context)
        if not acc_ids:
            # The category for this year does not yet exist
            acc_ids = [analytics_obj.create(cr, uid, {
                'name': year,
                'type': 'view',
                'code': 'AA' + event_type[:2].upper() + year,
                'parent_id': categ_id
            }, context)]
        return acc_ids[0]

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
