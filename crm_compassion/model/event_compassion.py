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

from openerp import api, models, fields, exceptions, _

from datetime import datetime


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def unlink(self):
        """ Override unlink to recompute expense/income of events. """
        analytic_lines = self.env['account.analytic.line'].search(
            [('move_id', 'in', self.ids)])
        account_ids = analytic_lines.mapped('account_id.id')
        events = self.env['crm.event.compassion'].search([
            ('analytic_id', 'in', account_ids)])
        res = super(account_move_line, self).unlink()
        events._store_set_values([
            'total_income', 'total_expense', 'balance'])
        return res


class event_compassion(models.Model):
    """A Compassion event. """
    _name = 'crm.event.compassion'
    _description = 'Compassion event'
    _order = 'start_date desc'

    _inherit = ['mail.thread']

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(size=128, required=True, track_visibility='onchange')
    full_name = fields.Char(compute='_get_full_name')
    type = fields.Selection(
        'get_event_types', required=True, track_visibility='onchange')
    start_date = fields.Datetime(required=True)
    year = fields.Char(compute='_set_year', store=True)
    end_date = fields.Datetime()
    partner_id = fields.Many2one(
        'res.partner', 'Customer', track_visibility='onchange')
    zip_id = fields.Many2one('res.better.zip', 'Address')
    street = fields.Char(size=128)
    street2 = fields.Char(size=128)
    city = fields.Char(size=128)
    state_id = fields.Many2one('res.country.state', 'State')
    zip = fields.Char(size=24)
    country_id = fields.Many2one('res.country', 'Country')
    user_id = fields.Many2one(
        'res.users', 'Ambassador', track_visibility='onchange')
    staff_ids = fields.Many2many(
        'res.partner', 'partners_to_staff_event', 'event_id',
        'partner_id', 'Staff')
    description = fields.Text()
    analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account')
    origin_id = fields.Many2one('recurring.contract.origin', 'Origin')
    contract_ids = fields.One2many(
        'recurring.contract', related='origin_id.contract_ids', readonly=True)
    expense_line_ids = fields.One2many(
        'account.analytic.line', compute='_set_analytic_lines', readonly=True)
    income_line_ids = fields.One2many(
        'account.analytic.line', compute='_set_analytic_lines', readonly=True)
    total_expense = fields.Float(
        'Total expense', compute='_set_analytic_lines', readonly=True,
        store=True)
    total_income = fields.Float(
        compute='_set_analytic_lines', readonly=True, store=True)
    balance = fields.Float(
        compute='_set_analytic_lines', readonly=True, store=True)
    planned_sponsorships = fields.Integer(
        'Expected sponsorships', track_visibility='onchange')
    lead_id = fields.Many2one(
        'crm.lead', 'Opportunity', track_visibility='onchange')
    won_sponsorships = fields.Integer(
        related='origin_id.won_sponsorships', store=True)
    project_id = fields.Many2one('project.project', 'Project')
    use_tasks = fields.Boolean('Use tasks')
    parent_id = fields.Many2one(
        'account.analytic.account', 'Parent', track_visibility='onchange')
    # This field circumvents problem for passing parent_id in a subview.
    parent_copy = fields.Many2one(
        'account.analytic.account', related='parent_id')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.depends('analytic_id', 'analytic_id.line_ids',
                 'analytic_id.line_ids.amount')
    def _set_analytic_lines(self):
        line_obj = self.env['account.analytic.line']
        if self.analytic_id:
            expenses = line_obj.search([
                ('account_id', '=', self.analytic_id.id),
                ('amount', '<', '0.0')])
            incomes = line_obj.search([
                ('account_id', '=', self.analytic_id.id),
                ('amount', '>', '0.0')])
            expense = abs(sum(expenses.mapped('amount')))
            income = sum(incomes.mapped('amount'))
            self.expense_line_ids = expenses.ids
            self.income_line_ids = incomes.ids
            self.total_expense = expense
            self.total_income = income
            self.balance = income - expense
        elif not isinstance(self.id, models.NewId):
            self.expense_line_ids = False
            self.income_line_ids = False
            self.total_expense = 0.0
            self.total_income = 0.0
            self.balance = 0.0

    @api.one
    @api.depends('start_date')
    def _set_year(self):
        if self.start_date:
            self.year = self.start_date[:4]

    @api.one
    def _get_full_name(self):
        self.full_name = self.type.title() + ' ' + self.name + ' ' + self.year

    def get_event_types(self):
        return [
            ('stand', _("Stand")),
            ('concert', _("Concert")),
            ('presentation', _("Presentation")),
            ('meeting', _("Meeting")),
            ('sport', _("Sport event"))]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ When an event is created:
        - Format the name to remove year of it,
        - Create an analytic_account,
        - Create an origin for sponsorships.
        """
        # Avoid putting twice the date in linked objects name
        event_year = vals.get('start_date',
                              datetime.today().strftime('%Y'))[:4]
        event_name = vals.get('name', '0000')
        if event_name[-4:] == event_year:
            vals['name'] = event_name[:-4]
        elif event_name[-2:] == event_year[-2:]:
            vals['name'] = event_name[:-2]

        event = super(event_compassion, self).create(vals)

        # Create project for the tasks
        project_id = False
        if event.use_tasks:
            project_id = self.env['project.project'].with_context(
                from_event=True).create(event._get_project_vals())

        # Analytic account and Origin linked to this event
        analytic_id = self.env['account.analytic.account'].create(
            event._get_analytic_vals()).id
        origin_id = self.env['recurring.contract.origin'].create(
            event._get_origin_vals(analytic_id)).id
        event.with_context(no_sync=True).write({
            'origin_id': origin_id,
            'analytic_id': analytic_id,
            'project_id': project_id,
        })
        return event

    @api.multi
    def write(self, vals):
        """ Push values to linked objects. """
        super(event_compassion, self).write(vals)

        if not self.env.context.get('no_sync'):
            for event in self:
                if 'use_tasks' in vals and event.use_tasks:
                    project_id = self.env['project.project'].with_context(
                        from_event=True).create(event._get_project_vals()).id
                    event.write({'project_id': project_id})
                elif event.project_id:
                    event.project_id.write(event._get_project_vals())
                event.analytic_id.write(event._get_analytic_vals())
                if 'name' in vals:
                    # Only administrator has write access to origins.
                    self.env['recurring.contract.origin'].sudo().browse(
                        event.origin_id.id).write({'name': event.full_name})

        return True

    @api.multi
    def unlink(self):
        """Check that the event is not linked with expenses or won
        sponsorships."""
        for event in self:
            if event.contract_ids or event.balance:
                raise exceptions.Warning(
                    _('Not authorized action'),
                    _('The event is linked to expenses or sponsorships. '
                      'You cannot delete it.'))
            else:
                if event.project_id:
                    event.project_id.unlink()
                if event.analytic_id:
                    event.analytic_id.unlink()
                event.origin_id.unlink()
        return super(event_compassion, self).unlink()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def show_tasks(self):
        self.ensure_one()
        project_id = self.project_id.id
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
            'search_view_id': self.env['ir.model.data'].get_object_reference(
                'project', 'view_task_search_form')[1]
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_project_vals(self):
        """ Creates a new project based on the event.
        """
        members = self.env['res.users'].search(
            [('partner_id', 'in', self.staff_ids.ids)]).ids
        return {
            'name': self.full_name,
            'use_tasks': True,
            'analytic_account_id': self.analytic_id.id,
            'project_type': self.type,
            'user_id': self.user_id.id,
            'partner_id': self.partner_id.id,
            'members': [(6, 0, members)],   # many2many field
            'date_start': self.start_date,
            'date': self.end_date,
            'state': 'open',
        }

    def _get_analytic_vals(self):
        name = self.name
        parent_id = self.parent_id and self.parent_id.id
        if self.city:
            name += ' ' + self.city
        if not parent_id:
            parent_id = self._find_parent_analytic()
            super(event_compassion, self).write({'parent_id': parent_id})
        return {
            'name': name,
            'type': 'event',
            'event_type': self.type,
            'date_start': self.start_date,
            'date': self.end_date,
            'parent_id': parent_id,
            'use_timesheets': True,
            'partner_id': self.partner_id.id,
            'manager_id': self.user_id.id,
            'user_id': self.user_id.id,
        }

    def _get_origin_vals(self, analytic_id):
        return {
            'type': 'event',
            'event_id': self.id,
            'analytic_id': analytic_id,
        }

    def _find_parent_analytic(self):
        analytics_obj = self.env['account.analytic.account']
        categ_id = analytics_obj.search(
            [('name', 'ilike', self.type)], limit=1).id
        acc_id = analytics_obj.search(
            [('name', '=', self.year), ('parent_id', '=', categ_id)],
            limit=1).id
        if not acc_id:
            # The category for this year does not yet exist
            acc_id = analytics_obj.create({
                'name': self.year,
                'type': 'view',
                'code': 'AA' + self.type[:2].upper() + self.year,
                'parent_id': categ_id
            }).id
        return acc_id
