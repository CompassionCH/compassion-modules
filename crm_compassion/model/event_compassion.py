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
        res = {}
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            res[event.id] = event.start_date[0:4]
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
        'user_id': fields.many2one('res.users', _("Responsible")),
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
        new_id = super(event_compassion, self).create(cr, uid, vals, context)
        event = self.browse(cr, uid, new_id, context)
        if event.lead_id:
            event.lead_id.write({'event_id': new_id})

        project_id = self._create_project(cr, uid, event, context)
        analytic_id = self.pool.get('project.project').browse(
            cr, uid, project_id, context).analytic_account_id.id
        origin_obj = self.pool.get('recurring.contract.origin')
        origin_id = origin_obj.create(cr, uid, {
            'name': event.name + " " + event.start_date[:4],
            'type': 'event',
            'partner_id': event.partner_id.id,
            'event_id': new_id,
            'analytic_id': analytic_id,
        }, context)
        event.write({
            'origin_id': origin_id,
            'analytic_id': analytic_id,
            'project_id': project_id,
        })
        return new_id

    def create_from_gp(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        # Don't create project tasks for an old Event imported from GP.
        context['use_tasks'] = False
        return self.create(cr, uid, vals, context)

    def _create_project(self, cr, uid, event, context=None):
        """ Creates a new project based on the event.
        """
        year = event.start_date[2:4]
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        analytics_obj = self.pool.get('account.analytic.account')
        categ_id = analytics_obj.search(
            cr, uid, [('name', 'ilike', event.type)], context=ctx)[0]
        acc_ids = analytics_obj.search(
            cr, uid, [('name', '=', year), ('parent_id', '=', categ_id)],
            context=ctx)
        if not acc_ids:
            # The category for this year does not yet exist
            acc_ids = [analytics_obj.create(cr, uid, {
                'name': year,
                'type': 'view',
                'code': 'AA' + event.type[:2].upper() + year,
                'parent_id': categ_id
            }, context)]
        members = self.pool.get('res.users').search(
            cr, uid,
            [('partner_id', 'in', [p.id for p in event.staff_ids])],
            context=ctx)
        ctx['from_event'] = True
        project_id = self.pool.get('project.project').create(cr, uid, {
            'name': event.name + ' ' + event.start_date[:4],
            'use_tasks': ctx.get('use_tasks', True),
            'user_id': event.user_id.id,
            'partner_id': event.partner_id.id,
            'members': [(6, 0, members)],   # many2many field
            'date_start': event.start_date,
            'date': event.end_date,
            'parent_id': acc_ids[0],
            'project_type': event.type,
            'state': 'open' if ctx.get('use_tasks', True) else 'close',
        }, ctx)

        return project_id

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
