##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from datetime import datetime, timedelta


class WeeklyDemand(models.Model):
    _name = 'demand.weekly.demand'
    _inherit = 'compassion.mapped.model'
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

    total_demand = fields.Integer()
    total_resupply = fields.Integer()

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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_values(self):
        """ Returns the values of a given week. """
        self.ensure_one()
        return self.read([
            'week_start_date', 'week_end_date',
            'total_demand', 'total_resupply'])[0]

    def get_defaults(self):
        """ Returns the computation defaults in a dictionary. """
        demand = self.env['ir.config_parameter'].get_param(
            'child_compassion.default_demand', 0)
        resupply = self.env['ir.config_parameter'].get_param(
            'child_compassion.default_resupply', 0)
        return {
            'total_demand': demand,
            'total_resupply': resupply,
        }
