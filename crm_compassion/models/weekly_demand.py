# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import math

from openerp import api, models, fields
from datetime import datetime, timedelta


class WeeklyDemand(models.Model):
    _name = 'demand.weekly.demand'
    _description = 'Weekly Demand'
    _rec_name = 'week_start_date'
    _order = 'week_start_date asc, id desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    demand_id = fields.Many2one(
        'demand.planning', string='Demand Planning', readonly=True,
        ondelete='cascade'
    )
    week_start_date = fields.Date(required=True)
    week_end_date = fields.Date(required=True)
    period_locked = fields.Boolean(compute='_compute_period_locked',
                                   store=True)
    # Demand fields
    number_children_website = fields.Integer(
        'Web demand',
        default=lambda self: int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_web')))
    number_children_ambassador = fields.Integer(
        'Ambassadors demand',
        default=lambda self: int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_ambassador')))
    number_children_sub = fields.Integer(
        'SUB',
        default=lambda self: int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_sub')))
    number_children_events = fields.Integer(
        'Events demand',
        compute='_compute_demand_events', store=True)
    total_demand = fields.Integer(compute='_compute_demand_total', store=True)

    # Resupply fields
    average_unsponsored_web = fields.Float(
        'Web resupply',
        default=lambda self: self._default_unsponsored_web()
    )
    average_unsponsored_ambassador = fields.Float(
        'Ambassadors resupply',
        default=lambda self: self._default_unsponsored_ambassador()
    )
    average_cancellation = fields.Float(
        'Sponsorship cancellations',
        default=lambda self: self._default_cancellation()
    )
    average_sub_sponsorship = fields.Float(
        'SUB resupply',
        default=lambda self: self._default_sub_sponsorship()
    )
    resupply_events = fields.Integer(
        'Events resupply',
        compute='_compute_demand_events', store=True
    )
    total_resupply = fields.Integer(
        compute='_compute_resupply_total', store=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('week_start_date')
    @api.multi
    def _compute_period_locked(self):
        for week in self:
            date_week = fields.Datetime.from_string(week.week_start_date)
            if date_week:
                week.period_locked = date_week <= (datetime.today() +
                                                   timedelta(weeks=8))

    @api.depends('week_start_date', 'week_end_date')
    @api.multi
    def _compute_demand_events(self):
        days_before_event = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.days_allocate_before_event'))
        for week in self.filtered('week_start_date').filtered('week_end_date'):
            start_date = fields.Date.from_string(week.week_start_date) + \
                timedelta(days=days_before_event)
            end_date = fields.Date.from_string(week.week_end_date) + \
                timedelta(days=days_before_event)
            events = self.env['crm.event.compassion'].search([
                ('start_date', '>=', fields.Date.to_string(start_date)),
                ('start_date', '<=', fields.Date.to_string(end_date)),
            ])
            allocate = sum(events.mapped('number_allocate_children'))
            resupply = allocate - sum(events.mapped('planned_sponsorships'))
            if resupply < 0:
                allocate -= resupply
                resupply = 0
            week.number_children_events = allocate
            week.resupply_events = resupply

    @api.depends('number_children_website', 'number_children_ambassador',
                 'number_children_sub', 'number_children_events')
    @api.multi
    def _compute_demand_total(self):
        for week in self:
            week.total_demand = week.number_children_website + \
                week.number_children_ambassador + week.number_children_sub + \
                week.number_children_events

    @api.model
    def _default_unsponsored_web(self):
        """ Compute average of unsponsored children on the website since
        one year.
        """
        start_date = datetime.today() - timedelta(weeks=52)
        web_sponsored = self.env['recurring.contract'].search_count([
            ('channel', '=', 'internet'),
            ('start_date', '>=', fields.Date.to_string(start_date))
        ])
        allocate_per_week = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_web'))
        return allocate_per_week - (float(web_sponsored) / 52.0)

    @api.model
    def _default_unsponsored_ambassador(self):
        """ Compute average of unsponsored children from ambassadors since
        one year.
        """
        start_date = datetime.today() - timedelta(weeks=52)
        ambass_sponsored = self.env['recurring.contract'].search_count([
            ('origin_id.type', '=', 'partner'),
            ('origin_id.partner_id', '!=', False),
            ('start_date', '>=', fields.Date.to_string(start_date))
        ])
        allocate_per_week = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_ambassador'))
        return allocate_per_week - (float(ambass_sponsored) / 52.0)

    @api.model
    def _default_cancellation(self):
        """ Compute average of sponsor cancellations since one year. """
        start_date = datetime.today() - timedelta(weeks=52)
        cancellations = self.env['recurring.contract'].search_count([
            ('state', '=', 'terminated'),
            ('end_reason', '!=', '1'),
            ('end_date', '>=', fields.Date.to_string(start_date))
        ])
        return float(cancellations) / 52.0

    @api.model
    def _default_sub_sponsorship(self):
        """ Compute average of SUB since one year. """
        start_date = datetime.today() - timedelta(weeks=52)
        sub_sponsorship = self.env['recurring.contract'].search_count([
            ('origin_id.type', '=', 'sub'),
            ('start_date', '>=', fields.Date.to_string(start_date))
        ])
        allocate_per_week = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_web'))
        return allocate_per_week - (float(sub_sponsorship) / 52.0)

    @api.depends('average_unsponsored_web', 'average_cancellation',
                 'average_sub_sponsorship', 'resupply_events')
    @api.multi
    def _compute_resupply_total(self):
        for week in self:
            week.total_resupply = math.floor(
                week.average_unsponsored_web + week.average_sub_sponsorship +
                week.average_cancellation + week.resupply_events)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ If we had more sponsored children from the than
        what we predict to allocate based on the system setting, make the
        prevision larger. """
        if vals['average_unsponsored_web'] < 0:
            vals['number_children_website'] -= vals['average_unsponsored_web']
            vals['average_unsponsored_web'] = 0

        if vals['average_unsponsored_ambassador'] < 0:
            vals['number_children_ambassador'] -= vals[
                'average_unsponsored_ambassador']
            vals['average_unsponsored_ambassador'] = 0

        if vals['average_sub_sponsorship'] < 0:
            vals['number_children_sub'] -= vals['average_sub_sponsorship']
            vals['average_sub_sponsorship'] = 0

        return super(WeeklyDemand, self).create(vals)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_defaults(self):
        """ Returns the computation defaults in a dictionary. """
        web = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_web'))
        ambassador = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_ambassador'))
        sub = int(self.env['ir.config_parameter'].get_param(
            'crm_compassion.number_children_sub'))
        return {
            'number_children_website': web,
            'number_children_ambassador': ambassador,
            'number_children_sub': sub,
            'average_unsponsored_web': self._default_unsponsored_web(),
            'average_unsponsored_ambassador':
                self._default_unsponsored_ambassador(),
            'average_sub_sponsorship': self._default_sub_sponsorship(),
            'average_cancellation': self._default_cancellation(),
        }
