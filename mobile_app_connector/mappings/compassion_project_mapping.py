# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class MobileProjectMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.project'
    MAPPING_NAME = 'mobile_app_project'

    CONNECT_MAPPING = {
        'AddressStreet': 'street',
        'AirportDistance': 'closest_airport_distance',
        'AirportPreferredTransportation': 'transport_mode_to_airport',
        'AirportTravelTime': 'time_to_airport',
        'AllocatedSurvivalSlots': None,  # <- question
        'AnnualPrimarySchoolCostLocalCurrency': 'annual_primary_school_cost',
        'AnnualSecondarySchoolCostLocalCurrency':
            'annual_secondary_school_cost',
        'AvailableForVisits': 'available_for_visits',
        'AverageCoolestTemperature': 'average_coolest_temperature',
        'AverageWarmestTemperature': 'average_warmest_temperature',
        'ChildDevelopmentCenterName': 'child_center_original_name',
        'ChildDevelopmentCenterNameLocalLanguage': 'preferred_lang_id',
        'ChurchMinistry': 'ministry_ids',
        'City': 'city',
        'Climate': 'community_climate',
        'ClosestMajorCityEnglish': None,  # <- question
        'Cluster': 'cluster',
        'CognitiveActivities0To5': 'cognitive_activity_babies_ids',
        'CognitiveActivities12Plus': 'cognitive_activity_ados_ids',
        'CognitiveActivities6To11': 'cognitive_activity_kids_ids',
        'CommunityInvolvement': None,  # <- question
        'Community_Name': 'community_name',
        'CompassionConnectEnabled': None,
        'ComputersForBeneficiaryUse': 'nb_child_computers',
        'ComputersForStaffUse': 'nb_staff_computers',
        'CoolestMonth': 'coolest_month',
        'Country': ('country_id.name', 'res.country'),
        'CountryDivision': None,  # <- question
        'Country_Name': None,  # <- question
        'CulturalRitualsAndCustoms': 'cultural_rituals',
        'CurrentStageInQavahProcess': None,  # <- question
        'Denomination': 'church_denomination',
        'EconomicNeedDescription': 'economic_needs',
        'EducationalNeedDescription': 'education_needs',
        'ElectricalPowerAvailability': 'electrical_power',
        'Facilities': 'facility_ids',
        'FacilityOwnershipStatus': 'church_ownership',
        'FamilyMonthlyIncome': 'monthly_income',
        'FieldOffice_Country': ('field_office_id.country',
                                'compassion.field.office'),
        'FieldOffice_Name': ('field_office_id.name',
                             'compassion.field.office'),
        'FieldOffice_RegionName': ('field_office_id.region',
                                   'compassion.field.office'),
        'FirstLetterWritingMonth': 'first_scheduled_letter',
        'FirstPartnershipAgreementSignedDate': None,  # <- question
        'FloorArea': None,  # <- question
        'FoundationDate': 'church_foundation_date',
        'GPSLatitude': 'gps_latitude',
        'GPSLongitude': 'gps_longitude',
        'HarvestMonths': 'harvest_month_ids',
        'HealthContextNeeds': 'health_needs',
        'HomeBasedSponsorshipBeneficiaries': None,  # <- question
        'HomeFloor': 'typical_floor_material',
        'HomeRoof': 'typical_roof_material',
        'HomeWall': 'typical_wall_material',
        'HungerMonths': 'hunger_month_ids',
        'ICPStatus': 'status',
        'ICP_ID': 'icp_id',
        'ICP_Name': 'local_church_name',
        'ICP_NameNonLatin': 'local_church_original_name',
        'ImplementedProgram': 'implemented_program_ids',
        'InterestedGlobalPartnerName': 'interested_partner_ids',
        'InternationalDenominationAffiliation': 'international_affiliation',
        'InternetAccess': 'church_internet_access',
        'IsParticipatingInQavahProcess': None,  # <- question
        'LastReviewedDate': 'last_reviewed_date',
        'LocaleType': 'community_locale',
        'MajorRevision_RevisedValues': None,  # <- question
        'MobileInternetAccess': 'mobile_device_ids',
        'MonthSchoolYearBegins': 'school_year_begins',
        'NumberOfActiveMembers': 'number_church_members',
        'NumberOfClassrooms': 'nb_classrooms',
        'NumberOfLatrines': 'nb_latrines',
        'NumberOfSponsorshipBeneficiaries': None,  # <- question
        'NumberOfSurvivalBeneficiaries': None,  # <- question
        'OnSiteInternetQuality': None,  # <- question
        'PhysicalActivities0To5': 'physical_activity_babies_ids',
        'PhysicalActivities12Plus': 'physical_activity_ados_ids',
        'PhysicalActivities6To11': 'physical_activity_kids_ids',
        'PlantingMonths': 'planting_month_ids',
        'Population': 'community_population',
        'PostalCode': 'zip_code',
        'PreferredLanguage': 'preferred_lang_id',
        'PrimaryDiet': 'primary_diet_ids',
        'PrimaryEthnicGroup': 'primary_ethnic_group_name',
        'PrimaryLanguage': 'primary_language_id',
        'PrimaryOccupation': 'primary_adults_occupation_ids',
        'ProgramBreakReason': None,  # <- question
        'ProgramBreakStartDate': None,  # <- question
        'ProgramEndDate': 'program_end_date',
        'ProgramStartDate': 'program_start_date',
        'ProgramsOfInterest': 'interested_program_ids',
        'ProjectActivitiesForFamilies': None,  # <- question
        'RainyMonths': 'rainy_month_ids',
        'SchoolCostPaidByICP': 'school_cost_paid_ids',
        'SecondLetterWritingMonth': 'second_scheduled_letter',
        'SocialMedia': 'social_media_site',
        'SocialNeedsDescription': 'social_needs',
        'SocioEmotionalActivities0To5': 'socio_activity_babies_ids',
        'SocioEmotionalActivities12Plus': 'socio_activity_ados_ids',
        'SocioEmotionalActivities6To11': 'socio_activity_kids_ids',
        'SourceKitName': None,  # <- question
        'SpiritualActivities0To5': 'spiritual_activity_babies_ids',
        'SpiritualActivities12Plus': 'spiritual_activity_ados_ids',
        'SpiritualActivities6To11': 'spiritual_activity_kids_ids',
        'Terrain': 'community_terrain',
        'Territory': 'territory',
        'TranslationCompletedFields': None,  # <- question
        'TranslationRequiredFields': None,  # <- question
        'TranslationStatus': None,  # <- question
        'TravelTimeToMedicalServices': 'time_to_medical_facility',
        'UnemploymentRate': 'unemployment_rate',
        'UtilitiesOnSite': 'utility_ids',
        'WarmestMonth': 'warmest_month',
        'Website': 'website',
        'WeeklyChildAttendance': 'weekly_child_attendance',
        'icpbio': None,  # <- question
        'icpbioInHtml': None  # <- question
    }

    FIELDS_TO_SUBMIT = {k: None for k, v in CONNECT_MAPPING.iteritems() if v}
