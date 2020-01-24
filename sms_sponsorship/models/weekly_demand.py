##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class WeeklyDemand(models.Model):
    _inherit = 'demand.weekly.demand'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends('week_start_date', 'week_end_date')
    @api.multi
    def _compute_demand_events(self):
        super()._compute_demand_events()
        for week in self.filtered('week_start_date').filtered('week_end_date'):
            # ADD SMS demand to the previsions
            events = self.env['crm.event.compassion'].search([
                ('start_date', '<=', week.week_end_date),
                ('start_date', '>', week.week_start_date),
                ('accepts_sms_booking', '=', True),
            ])
            allocate = sum(events.mapped('sms_number_hold_target'))
            week.number_children_events += allocate
            # We allocate more children for SMS but we won't make more
            # sponsorships than what is already planned, so it means we
            # can simply add the allocate number to the resupply number as well
            week.resupply_events += allocate
