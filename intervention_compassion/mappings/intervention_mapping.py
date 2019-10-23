##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.message_center_compassion.mappings.base_mapping \
    import OnrampMapping


class InterventionMapping(OnrampMapping):
    """ This class contains the mapping between Odoo fields and GMC field
    names for the model .
    """

    ODOO_MODEL = 'compassion.intervention'
    MAPPING_NAME = 'intervention_mapping'

    CONNECT_MAPPING = {
        "FieldOffice_Name":
            ('field_office_id.name', 'compassion.field.office'),
        "ActualLocalContribution": 'local_contribution',
        "EstimatedLocalContributionUSD": 'estimated_local_contribution',
        "TotalActualCostsUSD": 'total_cost',
        "TotalEstimatedCostsUSD": 'estimated_costs',
        "InterventionCategory_Name":
            ('category_id.name', 'compassion.intervention.category'),
        "InterventionSubCategory_Name":
            ('subcategory_id.name', 'compassion.intervention.subcategory'),
        "ActualDurationInMonthsNbr": 'actual_duration',
        "ActualEndDate": 'end_date',
        "AdditionalMarketingInformation":
            'additional_marketing_information',
        "ApprovedSLACostUSD": 'approved_sla_costs',
        "BackgroundInformation": 'background_information',
        "CancellationReason": 'cancel_reason',
        "CurrentPlannedEndDate": 'planned_end_date',
        "Description": 'description',
        "EstimatedImpactedBeneficiaryQuantity":
            'estimated_impacted_beneficiaries',
        "ExpectedDurationMonths": 'expected_duration',
        "FundingGlobalPartners": 'funding_global_partners',
        "FundingStatus": 'funding_status',
        "GlobalPartnerRequestedDeliverables": (
            'deliverable_level_3_ids.name',
            'compassion.intervention.deliverable'),
        "GlobalPartnerSelectedDeliverables": (
            'deliverable_level_2_ids.name',
            'compassion.intervention.deliverable'),
        "GlobalPartnerLevel2Selection": "sla_selection_complete",
        "ICP": ('fcp_ids.fcp_id', 'compassion.project'),
        "Intervention_ID": 'intervention_id',
        "ImpactedBeneficiaryQuantity": 'impacted_beneficiaries',
        "ImplementationRisks": 'implementation_risks',
        "InitialPlannedEndDate": 'initial_planned_end_date',
        "IsFieldOfficePriority": 'is_fo_priority',
        "LocalContributionUSD": 'local_contribution',
        "Intervention_Name": 'name',
        "NotFundedImplications": 'not_funded_implications',
        "Objectives": 'objectives',
        "ParentInterventionName": 'parent_intervention_name',
        "ProblemStatement": 'problem_statement',
        "ProposedSLACostUSD": 'fo_proposed_sla_costs',
        "ProposedStartDate": 'proposed_start_date',
        "RecordType": 'type',
        "SLAAdditionalComments": 'sla_comments',
        "SLANegotiationStatus": 'sla_negotiation_status',
        "ServiceLevel": 'service_level',
        "Solutions": 'solutions',
        "StartDate": 'start_date',
        "StartNoLaterThanDate": 'start_no_later_than',
        "Status": 'intervention_status',
        "SuccessFactors": 'success_factors',
        "TotalActualCosts": 'total_actual_cost_local',
        "TotalEstimatedCost": 'total_estimated_cost_local',
        "ProgramActivitiesFirstDayDate": 'start_date',

        # Additional field used by InterventionHoldRemovalNotification
        "InterventionType_Name": 'type',
        "ExpirationDate": 'expiration_date',
        "NotificationReason": 'cancel_reason',
        "HoldAmount": 'hold_amount',
        "PrimaryOwner": ('user_id.name', 'res.users'),
        "SecondaryOwner": 'secondary_owner',
        "InterventionHold_ID": 'hold_id',

        # Survival fields
        "AllocatedSurvivalSlots": 'survival_slots',
        "ReasonsForLaunch": 'launch_reason',
        "MotherAndChildrenChallenges": 'mother_children_challenges',
        "DesiredCommuniyBenefits": 'community_benefits',
        "FirstTimeMothersAverageAge": 'mother_average_age',
        "HouseholdChildrenAverageQuantity": 'household_children_average',
        "PopulationUnderAge5": 'under_five_population',
        "MedicalFacilityBirthPercent": 'birth_medical',
        "SpiritualActivities": ('spiritual_activity_ids.name',
                                'fcp.spiritual.activity'),
        "SocioEmotionalActivities": ('socio_activity_ids.name',
                                     'fcp.spiritual.activity'),
        "CognitiveVocationalActivities": ('cognitive_activity_ids.name',
                                          'fcp.spiritual.activity'),
        "OtherActivities": 'other_activities',
        "ParentFamilyActivities": 'activities_for_parents',
        "PhysicalHealthActivities": ('physical_activity_ids.name',
                                     'fcp.spiritual.activity'),

        # Not used in odoo:
        "Beneficiary_ProgramFieldManualExemption": None,
        "Case_ApprovedDate": None,
        "Case_ID": None,
        "Case_RequestedDate": None,
        "FieldOffice_Currency": None,
        "GlobalPartner_Name": None,
        "CenterBasedMinimumAge": None,
        "HomeBasedMaximumAge": None,
        "HomeBasedMinimumAge": None,
        "ActualCostPerBeneficiaryUSD": None,
        "EstimatedCostPerBeneficiaryUSD": None,
        "EstimatedLocalContribution": None,
        "AdditionalFundsCommitted": None,
        "ApprovedDate": None,
        "ContractorInformation": None,
        "FiscalYear": None,
        "FocusAreaNumber": None,
        "FundCode": None,
        "FundingStatusCommittedDate": None,
        "InitiationType": None,
        "IsIncludedInInterventionStrategy": None,
        "LeadershipApproval": None,
        "LinkToFieldOfficeStrategy": None,
        "MonthFundsRequested": None,
        "MonthOfNBRAllocation": None,
        "ProgramType": None,
        "ProposedSLACost": None,
        "RequestedAdditionalFundingUSD": 'requested_additional_funding',
        "SLAPreferenceSubmittedByUser": None,
        "Supporter": None,
        "SurvivalInterventionDesignation": None,
        "TopThreeAnticipatedExpenses": None,
        "SourceKitName": None,
        "Supporter_GlobalID": None,
        "InterventionReportingMilestone_ID": None,
        "Intervention_RecordTypeID": None,
        "DueDate": None,
        "HoldID": 'hold_id',
        "HoldReason": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": 'CH',
    }

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Split FCP ids"""
        if connect_name == 'ICP':
            value = value.split("; ")
        return super()._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )
