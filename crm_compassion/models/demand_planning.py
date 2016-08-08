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
    _rec_name = 'week_start_date'

    demand_ids = fields.Many2many(
        'demand.planning', string='Demand Planning', readonly=True
    )
    week_start_date = fields.Date(required=True)
    week_end_date = fields.Date(required=True)
    total_demand = fields.Float(required=True)
    resupply = fields.Float(required=True)
    period_locked = fields.Boolean(compute='_compute_period_locked',
                                   store=True)

    @api.depends('week_start_date')
    @api.multi
    def _compute_period_locked(self):
        for week in self:
            date_week = fields.Datetime.from_string(week.week_start_date)
            if date_week:
                week.period_locked = date_week <= (datetime.today() +
                                                   timedelta(weeks=8))


class DemandPlanning(models.Model):
    _name = 'demand.planning'
    _description = 'Demand Planning'
    _rec_name = 'date'

    date = fields.Date(
        default=lambda self: fields.Date.today(), readonly=True,
        states={'draft': [('readonly', False)]}
    )
    sent_date = fields.Datetime(readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], readonly=True, default='draft')
    weekly_demand_ids = fields.Many2many(
        'demand.weekly.demand', string='Weekly Demands', readonly=True,
        states={'draft': [('readonly', False)]}
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send_planning(self):
        self.ensure_one()
        message_obj = self.env['gmc.message.pool']

        action_id = self.env.ref(
            'crm_compassion.create_demand_planning').id
        object_id = self.id
        message_vals = {
            'action_id': action_id,
            'object_id': object_id
        }
        pool = message_obj.with_context(async_mode=False).create(message_vals)

        if pool.failure_reason:
            self.write({
                'state': 'error',
                'sent_date': fields.Datetime.now()
            })
            self.env.cr.commit()
            raise Warning("Error", pool.failure_reason)

        return self.write({
            'state': 'sent',
            'sent_date': fields.Datetime.now()
        })

    @api.multi
    def reset(self):
        return self.write({
            'state': 'draft',
            'sent_date': False
        })
