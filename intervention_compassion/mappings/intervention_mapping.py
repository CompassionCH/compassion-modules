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

    # TODO
    CONNECT_MAPPING = {
        "Beneficiary_ProgramFieldManualExemption": None,
        "Case_ApprovedDate": None,
        "Case_ID": None,
        "Case_RequestedDate": None,
        # "FieldOffice_Currency": "ETB (Birr)",  # ???
        "FieldOffice_Name":
            ('field_office_id.name', 'compassion.field.office'),
        "GlobalPartner_Name": None,
        "CenterBasedMinimumAge": None,
        "HomeBasedMaximumAge": None,
        "HomeBasedMinimumAge": None,
        "ActualCostPerBeneficiaryUSD": None,
        "ActualLocalContribution": 'local_contribution',
        "EstimatedCostPerBeneficiaryUSD": None,
        "EstimatedLocalContribution": None,
        "EstimatedLocalContributionUSD": 'estimated_local_contribution',
        "TotalActualCosts": None,
        "TotalActualCostsUSD": 'total_cost',
        "TotalEstimatedCost": 'estimated_costs',
        "TotalEstimatedCostsUSD": None,
        # generic
        "InterventionCategory_Name":
            ('category_id.name', 'compassion.intervention.category'),
        # generic
        "InterventionSubCategory_Name":
            ('subcategory_id.name', 'compassion.intervention.subcategory'),
        "ActualDurationInMonthsNbr": None,
        "ActualEndDate": 'end_date',
        # "AdditionalFundsCommitted": False,  # ???
        "AdditionalMarketingInformation":
            'additional_marketing_information',
        "AllocatedSurvivalSlots": None,
        "ApprovedDate": None,
        "ApprovedSLACostUSD": 'approved_sla_costs',
        # "AssociatedInactiveICPCount": 0,  # ???
        "BackgroundInformation": 'background_information',
        "CancellationReason": 'cancel_reason',
        "CognitiveVocationalActivities": None,
        "ContractorInformation": None,
        "CurrentPlannedEndDate": 'planned_end_date',
        "Description": 'description',
        "DesiredCommuniyBenefits": None,
        "EstimatedImpactedBeneficiaryQuantity":
            'estimated_impacted_beneficiaries',
        "ExpectedDurationMonths": 'start_date',
        # "FieldOfficeApprover": "ciITC1test5 ciITC1test5",  # ???
        "FirstTimeMothersAverageAge": None,
        "FiscalYear": None,
        "FocusAreaNumber": None,
        "FundCode": None,
        "FundingGlobalPartners": 'funding_global_partner_ids',
        "FundingStatus": 'funding_status',  # was "Fully Held", not known
        "FundingStatusCommittedDate": None,
        # "GlobalPartnerRequestedDeliverables": 'deliverable_ids',  # ???
        "GlobalPartnerSLA": None,
        "HouseholdChildrenAverageQuantity": None,
        "ICP": 'icp_id',  # generic, not sure
        "Intervention_ID": 'intervention_id',
        "ImpactedBeneficiaryQuantity": 'impacted_beneficiaries',
        "ImplementationRisks": 'implementation_risks',
        "InitialPlannedEndDate": 'initial_planned_end_date',
        "InitiationType": None,
        # "IsApproved": False,  # ???
        "IsFieldOfficePriority": 'is_fo_priority',
        # "IsICPSuspendedTerminated": False,  # ???
        # "IsIncludedInInterventionStrategy": False,  # ???
        "LeadershipApproval": None,
        "LinkToFieldOfficeStrategy": None,
        "LocalContributionUSD": None,
        "MedicalFacilityBirthPercent": None,
        "MonthFundsRequested": None,
        "MonthOfNBRAllocation": None,
        "MotherAndChildrenChallenges": None,
        "Intervention_Name": 'name',
        "NotFundedImplications": 'not_funded_implications',
        "Objectives": 'objectives',
        "OtherActivities": None,
        "ParentFamilyActivities": None,
        "PhysicalHealthActivities": None,
        "PopulationUnderAge5": None,
        "ProblemStatement": 'problem_statement',
        "ProgramActivitiesFirstDayDate": None,
        "ProgramType": None,
        "ProposedSLACost": None,
        "ProposedSLACostUSD": 'fo_proposed_sla_costs',
        "ProposedStartDate": 'proposed_start_date',
        "ReasonsForLaunch": None,
        "RecordType": 'type',
        # "RegionalApprover": "ciITC1test1 ciITC1test1",  # ???
        "RequestedAdditionalFundingUSD": None,
        "SLAAdditionalComments": None,
        "SLANegotiationStatus": 'sla_negotiation_status',
        "SLAPreferenceSubmittedByUser": None,
        "ServiceLevel": 'service_level',
        "SocioEmotionalActivities": None,
        "Solutions": 'solutions',
        "SpiritualActivities": None,
        "StartDate": 'start_date',
        "StartNoLaterThanDate": 'start_no_later_than',
        "Status": 'intervention_status',  # was "Submitted", not in list
        # "SubmittedDate": "2016-02-02",  # ???
        "SuccessFactors": 'success_factors',
        "Supporter": None,
        "SurvivalInterventionDesignation": None,
        # "TopThreeAnticipatedExpenses": [],  # ???
        # "SourceKitName": "InterventionKit",  # ???
        "Supporter_GlobalID": None,

        # mysterious field:
        "FieldOffice_Currency": None,
        "AdditionalFundsCommitted": None,
        "AssociatedInactiveICPCount": None,
        "FieldOfficeApprover": None,
        "GlobalPartnerRequestedDeliverables": None,
        "IsApproved": None,
        "IsICPSuspendedTerminated": None,
        "IsIncludedInInterventionStrategy": None,
        "RegionalApprover": None,
        "SubmittedDate": None,
        "TopThreeAnticipatedExpenses": None,
        "SourceKitName": None,
    }
