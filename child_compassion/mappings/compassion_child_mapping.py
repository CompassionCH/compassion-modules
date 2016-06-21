# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class GenericChildMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.generic.child'

    CONNECT_MAPPING = {
        # Fields used in Search Message (for global child)
        'Beneficiary_GlobalID': 'global_id',
        'Beneficiary_LocalID': 'local_id',
        'LocalNumber': 'local_id',
        'CorrespondentScore': 'correspondent_score',
        'IsSpecialNeeds': 'is_special_needs',
        'SourceCode': 'source_code',
        'PriorityScore': 'priority_score',
        'FullBodyImageURL': 'image_url',
        'MinDaysWaiting': 'waiting_days',

        # Fields for DetailedInformation message (for compassion.child)
        'GlobalId': 'global_id',
        'LocalBeneficiaryId': 'local_id',
        'AcademicPerformance_Name': 'academic_performance',
        'ActiveProgram': 'type',
        'Age': 'age',
        'BeneficiaryHousehold': ('household_id', 'compassion.household'),
        'BeneficiaryState': 'beneficiary_state',
        'BeneficiaryStatus': 'state',
        'Beneficiary_GlobalID': 'global_id',
        'Beneficiary_LocalID': 'local_id',
        'Beneficiary_LocalNumber': 'local_id',
        'BirthDate': 'birthdate',
        'Birthdate': 'birthdate',
        'CDSPType': 'cdsp_type',
        'ChristianActivity_Name': (
            'christian_activity_ids.name', 'child.christian.activity'),
        'ChronicIllness_Name': (
            'chronic_illness_ids.name', 'child.chronic.illness'),
        'CognitiveAgeGroup_Name': 'cognitive_age_group',
        'Community_Name': ('project_id.community_name', 'compassion.project'),
        'CompassChildID': 'compass_id',
        'CorrespondenceLanguage': 'correspondence_language',
        'CorrespondentScore': 'correspondent_score',
        'Country': (
            'project_id.field_office_id.country_id.code', 'res.country'),
        'CurrentUniversityYearOfStudy': 'university_year',
        'FO': ('project_id.name', 'compassion.project'),
        'FavoriteProjectActivity': (
            'activity_ids.name', 'child.project.activity'),
        'FavoriteSchoolSubject': ('subject_ids.name', 'child.school.subject'),
        'FieldOffice_Name': (
            'project_id.field_office_id.name', 'compassion.field.office'),
        'FirstName': 'firstname',
        'FormalEducationLevel': 'education_level',
        'FullBodyImageURL': 'image_url',
        'FullName': 'name',
        'Gender': 'gender',
        'GlobalId': 'global_id',
        'GradeLevelLocal_Name': 'local_grade_level',
        'GradeLevelUS_Name': 'local_grade_level',
        'HeightInCm': 'height',
        'HoldExpirationDate': 'hold_expiration_date',
        'HoldingGlobalPartner': (
            'holding_global_partner_id.name', 'compassion.global.partner'),
        'HouseholdDuty_Name': ('duty_ids.name', 'child.household.duty'),
        'ICPID': ('project_id.icp_id', 'compassion.project'),
        'ICP_ID': ('project_id.icp_id', 'compassion.project'),
        'IsBirthDateEstimated': 'estimated_birthdate',
        'IsInHIVAffectedArea': 'is_area_hiv_affected',
        'IsOrphan': 'is_orphan',
        'IsSpecialNeeds': 'is_special_needs',
        'LastName': 'lastname',
        'LastReviewDate': 'last_review_date',
        'LocalNumber': 'local_id',
        'MajorCourseOfStudy': 'major_course_study',
        'NameInNonLatinChar': 'non_latin_name',
        'NotEnrolledInEducationReason': 'not_enrolled_reason',
        'PhysicalDisability_Name': (
            'physical_disability_ids.name', 'child.physical.disability'),
        'PlannedCompletionDate': 'completion_date',
        'PreferredName': 'preferred_name',
        'PriorityScore': 'priority_score',
        'SourceCode': 'source_code',
        'SponsorshipStatus': 'sponsorship_status',
        'ThingsILike': ('hobby_ids.name', 'child.hobby'),
        'VocationalTrainingType_Name': 'vocational_training_type',
        'WaitingSinceDate': 'unsponsored_since',
        'WeightInKg': 'weight',

        # Not define
        'AgeInYearsAndMonths': None,
        'Cluster_Name': None,
        'Country_Name': None,
        'ExpectedTransitionDateToSponsorship': None,
        'FundType': None,
        'ICP_Name': None,
        'LocalBeneficiaryNumber': None,
        'MentalDevelopmentConditions': None,
        'PlannedCompletionDateChangeReason': None,
        'PrimaryCaregiverName': None,
        'ProgramDeliveryType': None,
        'RecordType_Name': None,
        'ReligiousAffiliation': None,
        'SponsoredStatus': 'sponsorship_status',
        'ThingsILikeAge1To2': ('hobby_ids.name', 'child.hobby'),
        'ThingsILikeAge3Plus': ('hobby_ids.name', 'child.hobby'),
        'TypeOfVocationalEducation': 'vocational_training_type',
        'USEquivalentGradeLevel': 'local_grade_level',
        'WeightInKg': 'weight',

        # Fields shared for both child types
        'Age': 'age',
        'BirthDate': 'birthdate',
        'ICP_ID': ('project_id.icp_id', 'compassion.project'),
        'FirstName': 'firstname',
        'LastName': 'lastname',
        'PreferredName': 'preferred_name',
        'FullName': 'name',
        'Gender': 'gender',
        'IsHivAffectedArea': 'is_area_hiv_affected',
        'IsOrphan': 'is_orphan',
        'WaitingSinceDate': 'unsponsored_since',
        'BeneficiaryState': 'beneficiary_state',
        'HoldingGlobalPartner': ('holding_global_partner_id.name',
                                 'compassion.global.partner'),
        'HoldExpirationDate': 'hold_expiration_date',
        'ReviewStatus': None,
        'SourceKitName': None,
        'UniversityYearOfStudy': None,
    }

    def _process_odoo_data(self, odoo_data):
        # Take first letter of gender
        gender = odoo_data.get('gender')
        if gender:
            odoo_data['gender'] = gender[0]

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Create compassion project if not existent. """
        result = super(GenericChildMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )
        if connect_name == 'ICP_ID' and not result.get('project_id'):
            project = self.env['compassion.project'].create({
                'icp_id': value
            })
            result['project_id'] = project.id
        return result


class GlobalChildMapping(GenericChildMapping):
    """ Mapping for Global Child object. """

    ODOO_MODEL = 'compassion.global.child'


class CompassionChildMapping(GenericChildMapping):
    ODOO_MODEL = 'compassion.child'
    MAPPING_NAME = 'GetDetails'

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    CONSTANTS = {
        'gpid': 'CH',
    }
