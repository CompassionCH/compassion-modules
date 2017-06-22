# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.addons.message_center_compassion.mappings.base_mapping \
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
        "ICP": ('icp_id.icp_id', 'compassion.project'),
        "Intervention_ID": 'intervention_id',
        "ImpactedBeneficiaryQuantity": 'impacted_beneficiaries',
        "ImplementationRisks": 'implementation_risks',
        "InitialPlannedEndDate": 'initial_planned_end_date',
        "IsFieldOfficePriority": 'is_fo_priority',
        "LocalContributionUSD": 'local_contribution',
        "Intervention_Name": 'name',
        "NotFundedImplications": 'not_funded_implications',
        "Objectives": 'objectives',
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

        # Additional field used by InterventionHoldRemovalNotification
        "InterventionType_Name": 'type',
        "ExpirationDate": 'expiration_date',
        "NotificationReason": 'cancel_reason',
        "HoldAmount": 'hold_amount',
        "PrimaryOwner": ('primary_owner.name', 'res.users'),
        "SecondaryOwner": 'secondary_owner',
        "InterventionHold_ID": 'hold_id',

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
        "TotalActualCosts": None,
        "TotalEstimatedCost": None,
        "AdditionalFundsCommitted": None,
        "AllocatedSurvivalSlots": None,
        "ApprovedDate": None,
        "CognitiveVocationalActivities": None,
        "ContractorInformation": None,
        "DesiredCommuniyBenefits": None,
        "FirstTimeMothersAverageAge": None,
        "FiscalYear": None,
        "FocusAreaNumber": None,
        "FundCode": None,
        "FundingStatusCommittedDate": None,
        "HouseholdChildrenAverageQuantity": None,
        "InitiationType": None,
        "IsIncludedInInterventionStrategy": None,
        "LeadershipApproval": None,
        "LinkToFieldOfficeStrategy": None,
        "MedicalFacilityBirthPercent": None,
        "MonthFundsRequested": None,
        "MonthOfNBRAllocation": None,
        "MotherAndChildrenChallenges": None,
        "OtherActivities": None,
        "ParentFamilyActivities": None,
        "PhysicalHealthActivities": None,
        "PopulationUnderAge5": None,
        "ProgramActivitiesFirstDayDate": None,
        "ProgramType": None,
        "ProposedSLACost": None,
        "ReasonsForLaunch": None,
        "RequestedAdditionalFundingUSD": 'requested_additional_funding',
        "SLAPreferenceSubmittedByUser": None,
        "SocioEmotionalActivities": None,
        "SpiritualActivities": None,
        "Supporter": None,
        "SurvivalInterventionDesignation": None,
        "TopThreeAnticipatedExpenses": None,
        "SourceKitName": None,
        "Supporter_GlobalID": None,
    }

    CONSTANTS = {
        "GlobalPartner_ID": 'CH',
    }
