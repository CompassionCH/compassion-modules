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

        'AcademicPerformance': 'academic_performance',
        'ActiveProgram': 'type',
        'AgeInYearsAndMonths': None,
        'BeneficiaryStatus': 'state',
        'Birthdate': 'estimated_birthdate',
        'CDSPType': 'cdsp_type',
        'ChristianActivities': (
            'christian_activity_ids.name', 'child.christian.activity'),
        'ChronicIllness': ('chronic_illness_ids.name',
                           'child.chronic.illness'),
        'CognitiveAgeGroup': 'cognitive_age_group',
        'CommunityName': ('project_id.community_name', 'compassion.project'),
        'CompassBeneficiaryID': 'compass_id',
        'CorrespondenceLanguage': 'correspondence_language',
        'CurrentUniversityYearOfStudy': 'university_year',
        'EstimatedBirthDate': 'estimated_birthdate',
        'ExpectedTransitionDateToSponsorship': None,
        'FO': ('project_id.name', 'compassion.project'),
        'FavoriteProjectActivities': ('activity_ids.name',
                                      'child.project.activity'),
        'FavoriteSubjectInSchool': (
            'subject_ids.name', 'child.school.subject'),
        'FormalEducationLevel': 'education_level',
        'HeightInCm': 'height',
        'HouseholdDuties': ('duty_ids.name', 'child.household.duty'),
        'HouseholdInformation': ('household_id', 'compassion.household'),
        'HouseholdMembersList': ('household_id.member_ids',
                                 'compassion.household.member'),
        'ICPID': ('project_id.icp_id', 'compassion.project'),
        'LastReviewedDate': 'last_review_date',
        'LocalBeneficiaryNumber': None,
        'LocalGradeLevel': 'local_grade_level',
        'MajorCourseOfStudy': 'major_course_study',
        'MentalDevelopmentConditions': None,
        'NameInNonLatinChar': 'non_latin_name',
        'NotEnrolledInEducationReason': 'not_enrolled_reason',
        'PhysicalDisabilities': ('physical_disability_ids.name',
                                 'child.physical.disability'),
        'PlannedCompletionDate': 'completion_date',
        'PlannedCompletionDateChangeReason': None,
        'PrimaryCaregiverName': None,
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
