# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class InterventionSearchMapping(OnrampMapping):
    """ Mapping for searching on the given fields. """
    ODOO_MODEL = 'compassion.global.intervention'
    MAPPING_NAME = 'search'

    CONNECT_MAPPING = {
        "Category": "category_id",
        "FieldOfficeID": "field_office_id",
        "FOPriority": None,
        "FirstDayOfProgramActivities": None,
        "FundingStatus": "funding_status",
        "GlobalPartnerId": None,
        "ICPId": "fcp_ids",
        "InterventionDescription": "description",
        "InterventionId": "intervention_id",
        "InterventionName": "name",
        "InterventionType": "type",
        "ParentIntervention": None,
        "ProposedStartDate": "proposed_start_date",
        "RemainingAvailableAmount_USD": "remaining_amount_to_raise",
        "SubCategory": "subcategory_id",
        "SupporterId": None,
        "SurvivalInterventionDesignation": None,
        "TotalEstimatedCost_USD": "estimated_costs",
    }

    FIELDS_TO_SUBMIT = {
    }


class GlobalInterventionMapping(OnrampMapping):
    """ Mapping for results of the search. """
    ODOO_MODEL = 'compassion.global.intervention'

    CONNECT_MAPPING = {
        "AdditionalMarketingInformation": "additional_marketing_information",
        "Intervention_Name": "name",
        "Intervention_ID": "intervention_id",
        "InterventionType": "type",
        "GlobalPartner_ID": ('holding_partner_id.code',
                             'compassion.global.partner'),
        "RemainingAmountToRaise": "remaining_amount_to_raise",
        "FundingStatus": "funding_status",
        "PlannedSponsorshipBeneficiariesNumber":
            'estimated_impacted_beneficiaries',
        "StartNoLaterThanDate": "start_no_later_than",
        "Description": "description",
        "InterventionCategory": ("category_id.name",
                                 "compassion.intervention.category"),
        "InterventionSubCategory_Name": (
            "subcategory_id.name", "compassion.intervention.subcategory"),
        "ProposedStartDate": "proposed_start_date",
        "ICP_ID": ("fcp_ids.fcp_id", "compassion.project"),
        "FieldOffice_ID": ("field_office_id.field_office_id",
                           "compassion.field.office"),
        "IsFieldOfficePriority": "is_fo_priority",
        "FundCode": None,
        "TotalInterventionAmount": 'total_cost',
        "TotalEstimatedCosts": "estimated_costs",
        "TotalPDCCost": 'pdc_costs',
        # TODO
        "AdditionalRequestedFunding": None,
        "ParentInterventionID": 'parent_intervention',
    }

    def _process_odoo_data(self, odoo_data):
        """ Find right category given the type of intervention. """
        if 'category_id' in odoo_data and 'type' in odoo_data:
            category_obj = self.env['compassion.intervention.category']
            selected_category = category_obj.browse(odoo_data['category_id'])
            category = category_obj.search([
                ('name', '=', selected_category.name),
                ('type', '=', odoo_data['type'])
            ])
            odoo_data['category_id'] = category.id
            del odoo_data['type']

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Split FCP ids"""
        if connect_name == 'ICP':
            value = value.split("; ")
        return super(GlobalInterventionMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )
