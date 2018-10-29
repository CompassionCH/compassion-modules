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
import re

from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ICPMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.project'

    CONNECT_MAPPING = {
        'AirportDistance': 'closest_airport_distance',
        'AirportPreferredTransportation': 'transport_mode_to_airport',
        'AirportTravelTime': 'time_to_airport',
        'AnnualPrimarySchoolCostLocalCurrency': 'annual_primary_school_cost',
        'AnnualSecondarySchoolCostLocalCurrency':
            'annual_secondary_school_cost',
        'AverageCoolestTemperature': 'average_coolest_temperature',
        'AverageWarmestTemperature': 'average_warmest_temperature',
        'Climate': 'community_climate',
        'ClosestMajorCityEnglish': 'closest_city',
        'CoolestMonth': 'coolest_month',
        'CulturalRitualsAndCustoms': 'cultural_rituals',
        'EconomicNeedDescription': 'economic_needs',
        'EducationalNeedDescription': 'education_needs',
        'FamilyMonthlyIncome': 'monthly_income',
        'HarvestMonths': ('harvest_month_ids.name', 'connect.month'),
        'HomeFloor': 'typical_floor_material',
        'HomeRoof': 'typical_roof_material',
        'HomeWall': 'typical_wall_material',
        'HungerMonths': ('hunger_month_ids.name', 'connect.month'),
        'LocaleType': 'community_locale',
        'MonthSchoolYearBegins': 'school_year_begins',
        'Community_Name': 'community_name',
        'PlantingMonths': ('planting_month_ids.name', 'connect.month'),
        'Population': 'community_population',
        'PrimaryDiet': ('primary_diet_ids.name', 'fcp.diet'),
        'PrimaryEthnicGroup': 'primary_ethnic_group_name',
        'PrimaryLanguage': ('primary_language_id.name', 'res.lang.compassion'),
        'PrimaryOccupation': ('primary_adults_occupation_ids.name',
                              'fcp.community.occupation'),
        'RainyMonths': ('rainy_month_ids.name', 'connect.month'),
        'SocialNeedsDescription': 'social_needs',
        'SpiritualNeedDescription': 'spiritual_needs',
        'Terrain': 'community_terrain',
        'TravelTimeToMedicalServices': 'time_to_medical_facility',
        'UnemploymentRate': 'unemployment_rate',
        'WarmestMonth': 'warmest_month',
        'Country': ('country_id.name', 'res.country'),
        'Denomination': 'church_denomination',
        'FieldOffice_Name': ('field_office_id.name',
                             'compassion.field.office'),
        'AddressStreet': 'street',
        'AvailableForVisits': 'available_for_visits',
        'ChildDevelopmentCenterName': 'name',
        'ChildDevelopmentCenterNameLocalLanguage':
            'child_center_original_name',
        'ChurchMinistry': ('ministry_ids.name', 'fcp.church.ministry'),
        'City': 'city',
        'Cluster': 'cluster',
        'CognitiveActivities0To5': ('cognitive_activity_babies_ids.name',
                                    'fcp.cognitive.activity'),
        'CognitiveActivities6To11': ('cognitive_activity_kids_ids.name',
                                     'fcp.cognitive.activity'),
        'CognitiveActivities12Plus': ('cognitive_activity_ados_ids.name',
                                      'fcp.cognitive.activity'),
        'CommunityInvolvement': ('involvement_ids.name', 'fcp.involvement'),
        'ComputersForBeneficiaryUse': 'nb_child_computers',
        'ComputersForStaffUse': 'nb_staff_computers',
        'CountryDivision': 'state_province',
        'ElectricalPowerAvailability': 'electrical_power',
        'Facilities': ('facility_ids.name', 'fcp.church.facility'),
        'FacilityOwnershipStatus': 'church_ownership',
        'FirstLetterWritingMonth': 'first_scheduled_letter',
        'FirstPartnershipAgreementSignedDate': 'partnership_start_date',
        'FloorArea': 'church_building_size',
        'FoundationDate': 'church_foundation_date',
        'GPSLatitude': 'gps_latitude',
        'GPSLongitude': 'gps_longitude',
        'HealthContextNeeds': 'health_needs',
        'ICPStatus': 'status',
        'ICP_ID': 'fcp_id',
        'ImplementedProgram': ('implemented_program_ids.name', 'fcp.program'),
        'InterestedGlobalPartnerName': ('interested_partner_ids.name',
                                        'fcp.program'),
        'InternationalDenominationAffiliation': 'international_affiliation',
        'InternetAccess': 'church_internet_access',
        'LastReviewedDate': 'last_reviewed_date',
        'ICP_Name': 'local_church_name',
        'ICP_NameNonLatin': 'local_church_original_name',
        'NumberOfActiveMembers': 'number_church_members',
        'NumberOfClassrooms': 'nb_classrooms',
        'NumberOfLatrines': 'nb_latrines',
        'NumberOfSponsorshipBeneficiaries': 'nb_cdsp_kids',
        'NumberOfSurvivalBeneficiaries': 'nb_csp_kids',
        'PhysicalActivities0To5': ('physical_activity_babies_ids.name',
                                   'fcp.physical.activity'),
        'PhysicalActivities6To11': ('physical_activity_kids_ids.name',
                                    'fcp.physical.activity'),
        'PhysicalActivities12Plus': ('physical_activity_ados_ids.name',
                                     'fcp.physical.activity'),
        'PostalCode': 'zip_code',
        'PreferredLanguage': ('preferred_lang_id.name', 'res.lang.compassion'),
        'ProgramEndDate': 'program_end_date',
        'ProgramStartDate': 'program_start_date',
        'ProgramsOfInterest': ('interested_program_ids.name', 'fcp.program'),
        'ProjectActivitiesForFamilies': 'activities_for_parents',
        'SchoolCostPaidByICP': ('school_cost_paid_ids.name',
                                'fcp.school.cost'),
        'SecondLetterWritingMonth': 'second_scheduled_letter',
        'SocialMedia': 'social_media_site',
        'SocioEmotionalActivities0To5': ('socio_activity_babies_ids.name',
                                         'fcp.sociological.activity'),
        'SocioEmotionalActivities6To11': ('socio_activity_kids_ids.name',
                                          'fcp.sociological.activity'),
        'SocioEmotionalActivities12Plus': ('socio_activity_ados_ids.name',
                                           'fcp.sociological.activity'),
        'SpiritualActivities0To5': ('spiritual_activity_babies_ids.name',
                                    'fcp.spiritual.activity'),
        'SpiritualActivities6To11': ('spiritual_activity_kids_ids.name',
                                     'fcp.spiritual.activity'),
        'SpiritualActivities12Plus': ('spiritual_activity_ados_ids.name',
                                      'fcp.spiritual.activity'),
        'Territory': 'territory',
        'UtilitiesOnSite': ('utility_ids.name', 'fcp.church.utility'),
        'Website': 'website',
        'WeeklyChildAttendance': 'weekly_child_attendance',

        # Not used in Odoo
        'AllocatedSurvivalSlots': None,
        'CompassionConnectEnabled': None,
        'CurrentStageInQavahProcess': None,
        'HomeBasedSponsorshipBeneficiaries': None,
        'IsParticipatingInQavahProcess': None,
        'MobileInternetAccess': None,
        'OnSiteInternetQuality': None,
        'ProgramBreakReason': None,
        'ProgramBreakStartDate': None,
        'TranslationCompletedFields': None,
        'TranslationRequiredFields': None,
        'TranslationStatus': None,
        'MajorRevision_RevisedValues': None,
        'SourceKitName': None,
    }

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    def __init__(self, env):
        super(ICPMapping, self).__init__(env)
        self.CONSTANTS = {'gpid': env.user.country_id.code}

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """
        Converts primary language to avoid lowercase / uppercase problems
        """
        if connect_name == 'PrimaryLanguage' and value:
            value = value.lower().title()
        return super(ICPMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )

    def _process_odoo_data(self, odoo_data):
        # Convert Project Status
        status = odoo_data.get('status')
        if status:
            status_mapping = {
                'Active': 'A',
                'Phase Out': 'P',
                'Suspended': 'S',
                'Transitioned': 'T',
            }
            odoo_data['status'] = status_mapping[status]

        for key in odoo_data.iterkeys():
            val = odoo_data[key]
            if isinstance(val, basestring) and val.lower() in (
                    'null', 'false', 'none', 'other', 'unknown'):
                odoo_data[key] = False

        monthly_income = odoo_data.get('monthly_income')
        if monthly_income:
            monthly_income = monthly_income.replace(',', '')
            # Replace all but last dot
            monthly_income = re.sub(r"\.(?=[^.]*\.)", "", monthly_income)
            # Replace any alpha character
            monthly_income = re.sub(r'[a-zA-Z$ ]', "", monthly_income)
            try:
                float(monthly_income)
                odoo_data['monthly_income'] = monthly_income
            except ValueError:
                # Weird value received, we prefer to ignore it.
                del odoo_data['monthly_income']
