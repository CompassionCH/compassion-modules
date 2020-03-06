##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, exceptions, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import math


class EventCompassion(models.Model):
    """A Compassion event. """
    _name = 'crm.event.compassion'
    _description = 'Compassion event'
    _order = 'start_date desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(size=128, required=True, track_visibility='onchange')
    full_name = fields.Char(compute='_compute_full_name')
    type = fields.Selection([
        ('stand', _("Stand")),
        ('concert', _("Concert")),
        ('presentation', _("Presentation")),
        ('meeting', _("Meeting")),
        ('sport', _("Sport event")),
        ('tour', _("Sponsor tour")),
    ], required=True, track_visibility='onchange')
    start_date = fields.Datetime(required=True)
    year = fields.Char(compute='_compute_year', store=True)
    end_date = fields.Datetime(required=True)
    partner_id = fields.Many2one(
        'res.partner', 'Customer', track_visibility='onchange', readonly=False)
    zip_id = fields.Many2one('res.better.zip', 'Address', readonly=False)
    street = fields.Char(size=128)
    street2 = fields.Char(size=128)
    city = fields.Char(size=128)
    state_id = fields.Many2one('res.country.state', 'State', readonly=False)
    zip = fields.Char(size=24)
    country_id = fields.Many2one('res.country', 'Country', readonly=False)
    user_id = fields.Many2one(
        'res.users', 'Ambassador', track_visibility='onchange', readonly=False)
    hold_ids = fields.One2many('compassion.hold',
                               'event_id',
                               readonly=True)
    allocate_child_ids = fields.One2many(
        'compassion.child',
        compute='_compute_allocate_children',
        string='Allocated children', readonly=False)
    effective_allocated = fields.Integer(compute='_compute_allocate_children')
    staff_ids = fields.Many2many(
        'res.partner', 'partners_to_staff_event', 'event_id', 'partner_id',
        'Staff', track_visibility='onchange', readonly=False)
    user_ids = fields.Many2many(
        'res.users', compute='_compute_users', track_visibility='onchange', readonly=False
    )
    description = fields.Text()
    analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account', copy=False, readonly=False)
    origin_id = fields.Many2one(
        'recurring.contract.origin', 'Origin', copy=False, readonly=False)
    contract_ids = fields.One2many(
        'recurring.contract', related='origin_id.contract_ids', readonly=True)
    expense_line_ids = fields.One2many(
        'account.analytic.line',
        compute='_compute_expense_lines', string='Expenses', readonly=False
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'event_id', readonly=True
    )
    income_line_ids = fields.One2many(
        'account.invoice.line',
        compute='_compute_income_lines', string='Income', readonly=False
    )
    total_expense = fields.Float(
        compute='_compute_expense', readonly=True, store=True)
    total_income = fields.Float(
        compute='_compute_income', readonly=True, store=True)
    balance = fields.Float(
        compute='_compute_balance', readonly=True, store=True)
    number_allocate_children = fields.Integer(
        'Number of children to allocate',
        track_visibility='onchange',
        required=True)
    planned_sponsorships = fields.Integer(
        'Expected sponsorships',
        track_visibility='onchange', required=True)
    lead_id = fields.Many2one(
        'crm.lead', 'Opportunity', track_visibility='onchange', readonly=False)
    won_sponsorships = fields.Integer(
        related='origin_id.won_sponsorships', store=True)
    conversion_rate = fields.Float(
        related='origin_id.conversion_rate', store=True)
    calendar_event_id = fields.Many2one('calendar.event', readonly=False)
    hold_start_date = fields.Date(required=True)
    hold_end_date = fields.Date()
    campaign_id = fields.Many2one('utm.campaign', 'Campaign', readonly=False)

    # Multi-company
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id.id, readonly=False
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_expense_lines(self):
        for event in self:
            event.expense_line_ids = event.analytic_id.line_ids.filtered(
                lambda l: l.amount < 0.0)

    @api.multi
    def _compute_income_lines(self):
        for event in self:
            event.income_line_ids = event.invoice_line_ids.filtered(
                lambda l: l.state == 'paid' and not l.contract_id and
                l.invoice_id.type == 'out_invoice'
            )

    @api.multi
    @api.depends('analytic_id.line_ids')
    def _compute_expense(self):
        for event in self:
            expenses = event.expense_line_ids.filtered(
                lambda l: l.amount < 0)
            event.total_expense = abs(sum(expenses.mapped('amount') or [0]))

    @api.multi
    @api.depends('invoice_line_ids.state')
    def _compute_income(self):
        for event in self:
            incomes = event.income_line_ids
            event.total_income = sum(incomes.mapped('price_subtotal') or [0])

    @api.multi
    @api.depends('total_income', 'total_expense')
    def _compute_balance(self):
        for event in self:
            if event.total_expense and event.total_income:
                event.balance = event.total_income / float(event.total_expense)
            else:
                event.balance = 0.0

    @api.multi
    @api.depends('start_date')
    def _compute_year(self):
        for event in self.filtered('start_date'):
            event.year = event.start_date[:4]

    @api.multi
    def _compute_full_name(self):
        for event in self:
            event.full_name = event.type.title() + ' ' + event.name + ' ' +\
                event.year

    @api.multi
    @api.depends('hold_ids')
    def _compute_allocate_children(self):
        for event in self:
            children = event.hold_ids.mapped('child_id')
            event.allocate_child_ids = children
            nb_child = 0
            for child in children:
                if child.state in ('N', 'I'):
                    nb_child += 1
            event.effective_allocated = nb_child

    @api.constrains('hold_start_date', 'start_date')
    def _check_hold_start_date(self):
        for event in self:
            if event.hold_start_date > event.start_date:
                raise ValidationError(
                    _("The hold start date must "
                      "be before the event starting date !"))

    @api.multi
    @api.depends('staff_ids')
    def _compute_users(self):
        for event in self:
            event.user_ids = event.staff_ids.mapped('user_ids').filtered(
                lambda u: not u.share)

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

        event = super().create(vals)

        # Analytic account and Origin linked to this event
        analytic_id = self.env['account.analytic.account'].create(
            event._get_analytic_vals()).id
        origin_id = self.env['recurring.contract.origin'].create(
            event._get_origin_vals(analytic_id)).id
        event.with_context(no_sync=True).write({
            'origin_id': origin_id,
            'analytic_id': analytic_id,
        })

        # Add calendar event
        calendar_event = self.env[
            'calendar.event'].create(event._get_calendar_vals())
        event.with_context(no_calendar=True).calendar_event_id = calendar_event

        return event

    @api.multi
    def write(self, vals):
        """ Push values to linked objects. """
        super().write(vals)
        if not self.env.context.get('no_sync'):
            for event in self:

                # Update Analytic Account and Origin
                event.analytic_id.write(event._get_analytic_vals())
                if 'user_id' in vals and event.origin_id:
                    event.origin_id.partner_id = event.user_id.partner_id

                if 'name' in vals:
                    # Only administrator has write access to origins.
                    self.env['recurring.contract.origin'].sudo().browse(
                        event.origin_id.id).write({'name': event.full_name})
                if not self.env.context.get('no_calendar'):
                    event.calendar_event_id.write(event._get_calendar_vals())

        return True

    @api.multi
    def copy(self, default=None):
        this_year = str(datetime.now().year)
        if self.year == this_year:
            if default is None:
                default = {}
            default['name'] = self.name + ' (copy)'
        return super().copy(default)

    @api.multi
    def unlink(self):
        """Check that the event is not linked with expenses or won
        sponsorships."""
        for event in self:
            if event.contract_ids or event.balance:
                raise exceptions.UserError(
                    _('The event is linked to expenses or sponsorships. '
                      'You cannot delete it.'))
            else:
                if event.analytic_id:
                    event.analytic_id.unlink()
                event.origin_id.unlink()
                event.calendar_event_id.unlink()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def update_calendar_events(self):
        """Put calendar event for old events missing it."""
        events = self.with_context(no_calendar=True).search([])
        calendar_obj = self.env['calendar.event']
        for event in events:
            calendar_vals = event._get_calendar_vals()
            if event.calendar_event_id:
                event.calendar_event_id.write(calendar_vals)
            else:
                calendar_event = calendar_obj.create(calendar_vals)
                event.calendar_event_id = calendar_event
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def show_sponsorships(self):
        self.ensure_one()
        return {
            'name': _('Sponsorships'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'recurring.contract',
            'src_model': 'crm.event.compassion',
            'context': self.with_context(default_type='S',
                                         group_by=False).env.context,
            'domain': [('id', 'in', self.origin_id.contract_ids.ids)],
        }

    @api.multi
    def show_expenses(self):
        self.ensure_one()
        return {
            'name': _('Expenses'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.analytic.line',
            'src_model': 'crm.event.compassion',
            'context': self.with_context(
                group_by='general_account_id').env.context,
            'domain': [('id', 'in', self.expense_line_ids.ids)],
        }

    @api.multi
    def show_income(self):
        return {
            'name': _('Income'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.invoice.line',
            'src_model': 'crm.event.compassion',
            'context': self.env.context,
            'domain': [('id', 'in', self.income_line_ids.ids)]
        }

    @api.multi
    def show_children(self):
        return {
            'name': _('Allocated Children'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'compassion.child',
            'src_model': 'crm.event.compassion',
            'context': self.with_context(
                search_default_available=1).env.context,
            'domain': [('id', 'in', self.allocate_child_ids.ids)]
        }

    @api.onchange('type')
    def onchange_type(self):
        """ Update analytic account """
        for event in self.filtered('type'):
            tag_ids = self.env['account.analytic.tag'].search([
                ('name', 'ilike', event.type)
            ]).ids
            event.analytic_id.write({
                'account_tag_ids': [(6, 0, tag_ids)]
            })

    @api.onchange('start_date')
    @api.multi
    def onchange_start_date(self):
        """ Update end_date and hold_start_date as soon as start_date is
        changed """
        days_allocate_before_event = self.env['res.config.settings'].sudo().get_param(
            'days_allocate_before_event')
        dt = timedelta(days=days_allocate_before_event)
        for event in self.filtered('start_date'):
            event.hold_start_date = event.start_date - dt
            if not event.end_date or event.end_date < event.start_date:
                event.end_date = event.start_date

    @api.onchange('end_date')
    @api.multi
    def onchange_end_date(self):
        days_after = self.env['res.config.settings'].sudo().get_param(
            'days_hold_after_event')
        for event in self.filtered('end_date'):
                hold_end_date = event.end_date + timedelta(days=days_after)
                event.hold_end_date = hold_end_date

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_analytic_vals(self):
        name = self.name
        tag_ids = self.env['account.analytic.tag'].search([
            ('name', 'ilike', self.type)
        ]).ids
        if self.city:
            name += ' ' + self.city
        return {
            'name': name,
            'year': self.year,
            'tag_ids': [(6, 0, tag_ids)],
            'partner_id': self.user_id.partner_id.id,
            'event_id': self.id
        }

    def _get_origin_vals(self, analytic_id):
        return {
            'type': 'event',
            'event_id': self.id,
            'analytic_id': analytic_id,
            'partner_id': self.user_id.partner_id.id
        }

    def _get_calendar_vals(self):
        """
        Gets the calendar event values given the event
        :return: dictionary of calendar.event values
        """
        self.ensure_one()
        time_delta = (self.end_date -
                      self.start_date)
        duration_in_hours = math.ceil(time_delta.days * 24 +
                                      time_delta.seconds / 3600.0)
        calendar_vals = {
            'name': self.name,
            'compassion_event_id': self.id,
            'categ_ids': [
                (6, 0, [self.env.ref('crm_compassion.calendar_event').id])],
            'duration': max(duration_in_hours, 3),
            'description': self.description,
            'location': self.city,
            'user_id': self.user_id.id,
            'partner_ids': [
                (6, 0, (self.staff_ids | self.partner_id |
                        self.user_id.partner_id).ids)],
            'start': self.start_date,
            'stop': self.end_date or self.start_date,
            'allday': self.end_date and (
                self.start_date[0:10] != self.end_date[0:10]),
            'state': 'open',  # to block that meeting date in the calendar
            'class': 'confidential',
        }
        return calendar_vals

    @api.multi
    def allocate_children(self):
        no_money_yield = float(self.planned_sponsorships)
        yield_rate = float(
            self.number_allocate_children - self.planned_sponsorships
        )
        if self.number_allocate_children > 1:
            no_money_yield /= self.number_allocate_children
            yield_rate /= self.number_allocate_children
        expiration_date = self.end_date + \
            timedelta(days=self.env['res.config.settings'].sudo()
                      .get_param('days_hold_after_event'))
        return {
            'name': _('Global Childpool'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'compassion.childpool.search',
            'target': 'current',
            'context': self.with_context({
                'default_take': self.number_allocate_children,
                'default_event_id': self.id,
                'default_channel': 'event',
                'default_ambassador': self.user_id.partner_id.id,
                'default_source_code': self.name,
                'default_no_money_yield_rate': no_money_yield*100,
                'default_yield_rate': yield_rate*100,
                'default_expiration_date':
                    expiration_date,
                'default_campaign_id': self.campaign_id.id
            }).env.context
        }

    ##########################################################################
    #              SUBSCRIPTION METHODS TO SUBSCRIBE STAFF ONLY              #
    ##########################################################################
    @api.multi
    def message_auto_subscribe(self, updated_fields, values=None):
        """
        Subscribe from user_ids field which is a computed field.
        """
        if 'staff_ids' in updated_fields and values:
            updated_fields = ['user_ids']
            for event in self:
                users = event.user_ids
                # Subscribe each staff individually
                ambassador = event.user_id
                for user in users:
                    # Hack to address the mail to the correct user, change
                    # user_id field(bypass ORM to avoid tracking field change)
                    self.env.cr.execute(
                        "UPDATE crm_event_compassion "
                        f"SET user_id = {user.id} WHERE id = {event.id}"
                    )
                    values = {'user_ids': user.id}
                    super(EventCompassion, event).message_auto_subscribe(
                        updated_fields, values
                    )
                # Restore ambassador
                user_id = "NULL"
                if ambassador.id:
                    user_id = ambassador.id
                self.env.cr.execute(
                    "UPDATE crm_event_compassion "
                    f"SET user_id = {user_id} WHERE id = {event.id}"
                )
        return True

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields,
                                           auto_follow_fields=None):
        """ Add user_ids field to followers """
        auto_follow_fields = ['user_ids']
        if 'staff_ids' in updated_fields:
            updated_fields.append('user_ids')
        return super()._message_get_auto_subscribe_fields(
            updated_fields, auto_follow_fields)
