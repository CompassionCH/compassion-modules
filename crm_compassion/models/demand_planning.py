##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime
from odoo import api, models


class DemandPlanning(models.Model):
    _inherit = 'demand.planning'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def process_weekly_demand(self):
        """ Weekly CRON for Demand Planning.
        3. Create last week revision
        """
        super().process_weekly_demand()
        today = datetime.today()
        last_week_demand = self.env['demand.weekly.demand'].search([
            ('week_end_date', '<', today),
            ('demand_id.state', '=', 'sent')
        ], order='week_end_date desc, id desc', limit=1)
        if last_week_demand:
            revision_obj = self.env['demand.weekly.revision']
            for type_tuple in revision_obj.get_revision_types():
                type = type_tuple[0]
                if type == 'web':
                    demand = last_week_demand.number_children_website
                    resupply = last_week_demand.average_unsponsored_web
                elif type == 'ambassador':
                    demand = last_week_demand.number_children_ambassador
                    resupply = last_week_demand.average_unsponsored_ambassador
                elif type == 'events':
                    demand = last_week_demand.number_children_events
                    resupply = last_week_demand.resupply_events
                elif type == 'sub':
                    demand = last_week_demand.number_sub_sponsorship
                    resupply = last_week_demand.resupply_sub
                elif type == 'cancel':
                    demand = 0
                    resupply = last_week_demand.average_cancellation
                revision_obj.create({
                    'week_start_date': last_week_demand.week_start_date,
                    'week_end_date': last_week_demand.week_end_date,
                    'type': type,
                    'demand': demand,
                    'resupply': resupply,
                })

        return True

    def _search_week(self, start_date):
        """
        Only look for period locked when submitting same values.
        All other weeks are computed each time.
        """
        search_filter = super()._search_week(start_date)
        search_filter.append(('period_locked', '=', True))
        return search_filter
