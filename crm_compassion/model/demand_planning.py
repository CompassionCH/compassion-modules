# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields
from datetime import datetime, timedelta


class WeeklyDemand(models.Model):

    _name = 'demand.weekly.demand'
    _description = 'Weekly Demand'

    name = fields.Char(required=True)
    demand_ids = fields.Many2many(
        'demand.planning', string='Demand Planning', readonly=True
    )
    week_start_date = fields.Date(required=True)
    week_end_date = fields.Date(required=True)
    total_demand = fields.Float(required=True)
    resupply = fields.Float(required=True)
    period_locked = fields.Boolean(default=False)

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.model
    def create(self, vals):
        vals = self.update_vals(vals)
        res = super(WeeklyDemand, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        vals = self.update_vals(vals)
        res = super(WeeklyDemand, self).write(vals)
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def update_vals(self, vals):
        starting_date = datetime.strptime(vals.get('week_start_date'),
                                          "%Y-%m-%d")
        if self.check_is_date_in_next_8_weeks(starting_date):
            vals['period_locked'] = True
        return vals

    def check_is_date_in_next_8_weeks(self, date):
        return date <= (datetime.today() + timedelta(weeks=8))


class DemandPlanning(models.Model):

    _name = 'demand.planning'
    _description = 'Demand Planning'

    name = fields.Char(required=True)
    date = fields.Date()
    sent_date = fields.Datetime()
    state = fields.Selection([
        ('new', 'New'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ])
    weekly_demand_ids = fields.Many2many(
        'demand.weekly.demand', string='Weekly Demands'
    )
