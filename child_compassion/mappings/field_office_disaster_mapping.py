# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ICPDisasterImpactMapping(OnrampMapping):
    """
    ICP Disaster Impact Mapping
    """
    ODOO_MODEL = 'icp.disaster.impact'

    CONNECT_MAPPING = {
        'Disaster_ImpactOnICPProgram': 'impact_on_icp_program',
        'Disaster_Name': ('fo_disaster_alert_id.disaster_name',
                          'fo.disaster.alert'),
        'ICPDisasterImpact_DisasterImpactDescription':
            'disaster_impact_description',
        'ICPDisasterImpact_ICPDisasterStatus': 'disaster_status',
        'ICPDisasterImpact_ICPInfrastructureDisasterImpact': 'infrastructure',
        'ICP_ID': 'project_id',
        # 'ICP_Name': '',
    }


class FieldOfficeDisasterUpdate(OnrampMapping):
    """
    Field Office Disaster Update Mapping
    """
    ODOO_MODEL = 'fo.disaster.update'

    CONNECT_MAPPING = {
        'DisasterCommunicationUpdate_ID': 'fodu_id',
        'DisasterCommunicationUpdate_Name': 'name',
        'DisasterCommunicationUpdate_Summary': 'summary',
        'Disaster_Name': ('fo_disaster_alert_id.disaster_name',
                          'fo.disaster.alert'),
        'FieldOffice_Name': ('fo_id.name', 'compassion.field.office'),
    }


class ChildDisasterImpact(OnrampMapping):
    """
    Child Disaster Impact Mapping
    """
    ODOO_MODEL = 'child.disaster.impact'

    CONNECT_MAPPING = {
        'BeneficiaryLocation': 'beneficiary_location',
        'BeneficiaryPhysicalCondition': 'beneficiary_physical_condition',
        'CaregiversDiedNumber': 'caregivers_died_number',
        'CaregiversSeriouslyInjuredNumber':
            'caregivers_seriously_injured_number',
        'DisasterStatus': 'disaster_status',
        'HouseCondition': 'house_condition',
        'LostPersonalEffects': 'lost_personal_effects',
        'SiblingsDiedNumber': 'siblings_died_number',
        'SiblingsSeriouslyInjuredNumber': 'siblings_seriously_injured_number',
        # 'Beneficiary_FullName': '',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        # 'Beneficiary_LocalID': '',
        'Disaster_Name': ('fo_disaster_alert_id.disaster_name',
                          'fo.disaster.alert'),
        'SponsorshipStatus': 'sponsorship_status',
    }


class FieldOfficeDisasterMapping(OnrampMapping):
    """
    Field Office Mapping
    """
    ODOO_MODEL = 'fo.disaster.alert'
    MAPPING_NAME = 'field_office_disaster'

    CONNECT_MAPPING = {
        'BeneficiaryDisasterImpacts': ('child_disaster_impact_ids',
                                       'child.disaster.impact'),
        'DisasterCommunicationUpdates': ('fo_disaster_update_ids',
                                         'fo.disaster.update'),
        'AreaDescription': 'area_description',
        'CloseDate': 'close_date',
        'DisasterDate': 'disaster_date',
        'DisasterStatus': 'disaster_status',
        'DisasterType': 'disaster_type',
        'EstimatedBasicSuppliesNeeded': 'estimated_basic_supplies_needed',
        'EstimatedHomesDestroyed': 'estimated_homes_destroyed',
        'EstimatedLossOfLife': 'estimated_loss_of_life',
        'EstimatedLossOfLivelihood': 'estimated_loss_of_livelihood',
        'EstimatedNotAttendingProject': 'estimated_not_attending_project',
        'EstimatedRehabilitationFundsUSD':
            'estimated_rehabilitation_funds_usd',
        'EstimatedReliefFundsUSD': 'estimated_relief_funds_usd',
        'EstimatedSeriousInjuries': 'estimated_serious_injuries',
        'FieldOfficeDamage': 'field_office_damage',
        'FieldOfficeImpactDescription': 'field_office_impact_description',
        'Disaster_ID': 'disaster_id',
        'ImpactDescription': 'impact_description',
        'ImpactOnICPInfrastructureDamaged':
            'impact_on_icp_infrastructure_damaged',
        'ImpactOnICPInfrastructureDestroyed':
            'impact_on_icp_infrastructure_destroyed',
        'ImpactOnICPProgramTemporarilyClosed':
            'impact_on_icp_program_temporarily_closed',
        'ImpactToFieldOfficeOperations': 'impact_to_field_office_operations',
        'IsAdditionalFundsRequested': 'is_additional_funds_requested',
        'IsCommunicationSensitive': 'is_communication_sensitive',
        'IsEstimatedDamageOverOneMillionUSD':
            'is_estimated_damage_over_one_million_usd',
        'Disaster_Name': 'disaster_name',
        'ReportedLossOfLifeBeneficiaries':
            'reported_loss_of_life_beneficiaries',
        'ReportedLossOfLifeCaregivers':
            'reported_loss_of_life_caregivers',
        'ReportedLossOfLifeSiblings': 'reported_loss_of_life_siblings',
        'ReportedNumberBeneficiariesImpacted':
            'reported_number_beneficiaries_impacted',
        'ReportedNumberOfICPsImpacted': 'reported_number_of_icps_impacted',
        'ReportedSeriousInjuriesBeneficaries':
            'reported_serious_injuries_beneficiaries',
        'ReportedSeriousInjuriesCaregivers':
            'reported_serious_injuries_caregivers',
        'ReportedSeriousInjuriesSiblings':
            'reported_serious_injuries_siblings',
        'ResponseDescription': 'response_description',
        'SeverityLevel': 'severity_level',
        'FieldOffice_Name': ('field_office_id.name',
                             'compassion.field.office'),
        'ICPDisasterImpacts': ('icp_disaster_impact_ids',
                               'icp.disaster.impact'),
        'SourceKitName': 'source_kit_name',
    }
