##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime, timedelta
from odoo import api, models, fields


class DemandPlanning(models.Model):
    _name = 'demand.planning'
    _inherit = 'compassion.mapped.model'
    _description = 'Demand Planning'
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date(
        default=lambda self: fields.Date.today(), readonly=True,
        states={'draft': [('readonly', False)]}, copy=False
    )
    sent_date = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], readonly=True, default='draft')
    weekly_demand_ids = fields.One2many(
        'demand.weekly.demand', 'demand_id', string='Weekly Demands',
        default=lambda self: self._get_default_weekly_demands(),
        readonly=True, states={'draft': [('readonly', False)]},
        copy=True
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_default_weekly_demands(self):
        """ Take previous locked previsions and create new ones for future
        weeks. """
        create_values = list()
        today = datetime.today()
        sunday = today
        # Sunday weekday is 6
        diff_to_sunday = 6 - today.weekday()
        if diff_to_sunday:
            # Add extra week so we start creating previsions in 2 weeks
            sunday = today + timedelta(days=(diff_to_sunday + 7))

        # Submit 78 weeks
        for i in range(0, 78):
            vals = {}
            week_vals = (0, 0, vals)
            week_demand = self.env['demand.weekly.demand'].search(
                self._search_week(sunday), limit=1)
            if week_demand:
                # Locked period: resubmit same values as before
                vals.update(week_demand.get_values())
            else:
                end_date = (sunday + timedelta(days=6)).date()
                vals.update(self.env['demand.weekly.demand'].get_defaults())
                vals.update({
                    'week_start_date': sunday.date(),
                    'week_end_date': end_date
                })
            create_values.append(week_vals)
            sunday = sunday + timedelta(days=7)

        return create_values

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send_planning(self):
        message_obj = self.env['gmc.message']
        pool = message_obj
        action_id = self.env.ref('child_compassion.create_demand_planning').id

        for planning in self:
            message_vals = {
                'action_id': action_id,
                'object_id': planning.id
            }
            pool += message_obj.create(message_vals)

        pool.with_context(async_mode=False).process_messages()
        for i in range(0, len(pool)):
            self[i].write({
                'state': 'sent' if not pool[i].failure_reason else 'error',
                'sent_date': fields.Datetime.now()
            })

        return True

    @api.multi
    def reset(self):
        return self.write({
            'state': 'draft',
            'sent_date': False
        })

    @api.model
    def process_weekly_demand(self):
        """ Weekly CRON for Demand Planning.
        1. Submit previsions
        2. Create Demand Planning for the next weeks
        """
        next_week = datetime.today() + timedelta(days=7)
        previsions = self.search([
            ('state', '=', 'draft'),
            ('date', '<=', next_week)
        ])
        previsions.send_planning()

        self.create({
            'weekly_demand_ids': self._get_default_weekly_demands()
        })

        return True

    def _search_week(self, start_date):
        """
        Returns the search filter for finding a previous week demand to
        resubmit.
        :param start_date: Date of the week
        :return: Search filter for weekly.demand
        """
        return [
            ('week_start_date', '=', start_date),
        ]

    @api.model
    def json_to_data(self, json, mapping_name=None):
        connect_data = super().json_to_data(json, mapping_name)
        return {
            "GlobalPartnerWeeklyDemandRequest": connect_data,
            "GlobalPartner_ID": self.env.user.country_id.code
        }
