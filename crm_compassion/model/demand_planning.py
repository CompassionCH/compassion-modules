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
from openerp.exceptions import Warning

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
        self.update_vals(vals)
        res = super(WeeklyDemand, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        self.update_vals(vals)
        res = super(WeeklyDemand, self).write(vals)
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def update_vals(self, vals):
        starting_date = vals.get('week_start_date')
        if starting_date:
            corrected_date = datetime.strptime(starting_date, "%Y-%m-%d")
            if self.check_is_date_in_next_8_weeks(corrected_date):
                vals['period_locked'] = True
            else:
                vals['period_locked'] = False
        # return vals

    def check_is_date_in_next_8_weeks(self, date):
        return date <= (datetime.today() + timedelta(weeks=8))


class DemandPlanning(models.Model):
    _name = 'demand.planning'
    _description = 'Demand Planning'

    name = fields.Char(required=True)
    date = fields.Date()
    sent_date = fields.Datetime()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ])
    weekly_demand_ids = fields.Many2many(
        'demand.weekly.demand', string='Weekly Demands'
    )

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.model
    def create(self, vals):
        res = super(DemandPlanning, self).create(vals)
        res.state = 'draft'
        return res

    @api.multi
    def write(self, vals):
        res = super(DemandPlanning, self).write(vals)
        if not isinstance(res, bool):
            res.state = 'draft'
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send_planning(self):
        message_obj = self.env['gmc.message.pool']

        action_id = self.env.ref(
            'crm_compassion.create_demand_planning').id
        object_id = self.id
        message_vals = {
            'action_id': action_id,
            'object_id': object_id
        }
        pool = message_obj.with_context(async_mode=False,
                                        creating=True).create(message_vals)

        if pool.failure_reason:
            self.state = 'error'
            self.env.cr.commit()
            raise Warning("Error", pool.failure_reason)
        self.state = 'sent'
