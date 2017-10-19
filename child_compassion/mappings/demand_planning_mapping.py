# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class WeeklyDemandCreateMapping(OnrampMapping):
    """
    Weekly Demand mapping for the create operation
    """
    ODOO_MODEL = 'demand.weekly.demand'

    CONNECT_MAPPING = {
        'ResupplyQuantity': 'total_resupply',
        'TotalDemand': 'total_demand',
        'WeekEndDate': 'week_end_date',
        'WeekStartDate': 'week_start_date',
    }

    FIELDS_TO_SUBMIT = {
        'ResupplyQuantity': None,
        'TotalDemand': None,
        'WeekEndDate': None,
        'WeekStartDate': None,
    }


class DemandPlanningCreateMapping(OnrampMapping):
    """
    Demand Planning mapping for the create operation
    """
    ODOO_MODEL = 'demand.planning'
    MAPPING_NAME = "create_demand_planning"

    CONNECT_MAPPING = {
        'GlobalPartnerWeeklyDemandRequestList': ('weekly_demand_ids',
                                                 'demand.weekly.demand'),
    }

    FIELDS_TO_SUBMIT = {
        'GlobalPartnerWeeklyDemandRequestList': None,
        'GlobalPartner_ID': None,
    }

    CONSTANTS = {
        'GlobalPartner_ID': 'CH',
    }

    def _process_connect_data(self, connect_data):
        """ Wrap the message in a tag. """
        demand_data = connect_data.copy()
        connect_data.clear()
        connect_data['GlobalPartnerWeeklyDemandRequest'] = demand_data
