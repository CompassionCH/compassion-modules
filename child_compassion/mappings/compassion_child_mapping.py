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


class GenericChildMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.generic.child'

    CONNECT_MAPPING = {

        'LocalBeneficiaryId': 'local_id',
        'AcademicPerformance_Name': 'academic_performance',
        'ActiveProgram': 'type',
        'Age': 'age',
        'BeneficiaryHousehold': ('household_id', 'compassion.household'),
        'BeneficiaryHouseholdList': ('household_id', 'compassion.household'),
        'BeneficiaryState': 'beneficiary_state',
        'BeneficiaryStatus': 'beneficiary_state',
        'Beneficiary_Gender': 'gender',
        'Beneficiary_GlobalID': 'global_id',
        'Beneficiary_LocalID': 'local_id',
        'Beneficiary_LocalNumber': None,
        'BirthDate': 'birthdate',
        'Birthdate': 'birthdate',
        'CDSPType': 'cdsp_type',
        'ProgramDeliveryType': 'cdsp_type',
        'ChristianActivity_Name': (
            'christian_activity_ids.name', 'child.christian.activity'),
        'ChronicIllness': (
            'chronic_illness_ids.name', 'child.chronic.illness'),
        'ChronicIllness_Name': (
            'chronic_illness_ids.name', 'child.chronic.illness'),
        'CognitiveAgeGroup_Name': 'cognitive_age_group',
        'CompassChildID': 'compass_id',
        'CompassID': 'compass_id',
        'CorrespondenceLanguage': ('correspondence_language_id.name',
                                   'res.lang.compassion'),
        'CorrespondentScore': 'correspondent_score',
        'CurrentUniversityYearOfStudy': 'university_year',
        'FavoriteProjectActivity': (
            'activity_ids.name', 'child.project.activity'),
        'FavoriteSchoolSubject': ('subject_ids.name', 'child.school.subject'),
        'FirstName': 'firstname',
        'FormalEducationLevel': 'education_level',
        'FullBodyImageURL': 'image_url',
        'FullName': 'name',
        'Gender': 'gender',
        'GlobalId': 'global_id',
        'GradeLevelLocal_Name': 'local_grade_level',
        'GradeLevelUS_Name': 'us_grade_level',
        'HeightInCm': 'height',
        'HoldExpirationDate': 'hold_expiration_date',
        'HoldingGlobalPartner': (
            'holding_global_partner_id.name', 'compassion.global.partner'),
        'HoldingGlobalPartnerID': (
            'holding_global_partner_id.country_id.code',
            'compassion.global.partner'),
        'HouseholdDuty_Name': ('duty_ids.name', 'child.household.duty'),
        'ICPID': ('project_id.fcp_id', 'compassion.project'),
        'ICP_ID': ('project_id.fcp_id', 'compassion.project'),
        'IsHivAffectedArea': 'is_area_hiv_affected',
        'IsBirthDateEstimated': 'estimated_birthdate',
        'IsInHIVAffectedArea': 'is_area_hiv_affected',
        'IsOrphan': 'is_orphan',
        'IsSpecialNeeds': 'is_special_needs',
        'LastName': 'lastname',
        'LastPhotoDate': 'last_photo_date',
        'LastReviewDate': 'last_review_date',
        'LocalNumber': 'local_id',
        'MajorOrCourseOfStudy': 'major_course_study',
        'MinDaysWaiting': 'waiting_days',
        'NameInNonLatinChar': 'non_latin_name',
        'NotEnrolledInEducationReason': 'not_enrolled_reason',
        'PhysicalDisability': (
            'physical_disability_ids.name', 'child.physical.disability'),
        'PhysicalDisability_Name': (
            'physical_disability_ids.name', 'child.physical.disability'),
        'PlannedCompletionDate': 'completion_date',
        'PlannedCompletionDateChangeReason': 'completion_date_change_reason',
        'PreferredName': 'preferred_name',
        'PriorityScore': 'priority_score',
        'RevisedValues': 'revised_value_ids',
        'SourceCode': 'source_code',
        'SponsorshipStatus': 'sponsorship_status',
        'SponsoredStatus': 'sponsorship_status',
        'ThingsILike': ('hobby_ids.name', 'child.hobby'),
        'ThingsILikeAge1To2': ('hobby_ids.name', 'child.hobby'),
        'ThingsILikeToDoAge3Plus': ('hobby_ids.name', 'child.hobby'),
        'TypeOfVocationalEducation': 'vocational_training_type',
        'USEquivalentGradeLevel': 'us_grade_level',
        'VocationalTrainingType_Name': 'vocational_training_type',
        'WaitingSinceDate': 'unsponsored_since',
        'WeightInKg': 'weight',

        # Not define
        'AgeInYearsAndMonths': None,
        'Beneficiary_FundType': None,
        'Cluster_Name': None,
        'Community_Name': None,
        'Country': None,
        'Country_Name': None,
        'ExpectedTransitionDateToSponsorship': None,
        'FieldOffice_Name': None,
        'FO': None,
        'FundType': None,
        'ICP_Country': None,
        'ICP_Name': None,
        'LocalBeneficiaryNumber': None,
        'MentalDevelopmentConditions': None,
        'PrimaryCaregiverName': None,
        'RecordType_Name': None,
        'ReligiousAffiliation': None,
        'ReviewStatus': None,
        'SourceKitName': None,
        'UniversityYearOfStudy': None,
    }

    def _process_odoo_data(self, odoo_data):
        # Take first letter of gender
        gender = odoo_data.get('gender')
        if gender:
            odoo_data['gender'] = gender[0]
        # Put firstname in preferred_name if not defined
        preferred_name = odoo_data.get('preferred_name')
        if not preferred_name:
            odoo_data['preferred_name'] = odoo_data.get('firstname')
        # Remove invalid data
        for key in odoo_data.iterkeys():
            val = odoo_data[key]
            if isinstance(val, basestring) and val.lower() in (
                    'null', 'false', 'none', 'other', 'unknown'):
                odoo_data[key] = False

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Create compassion project if not existent. """
        result = super(GenericChildMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )
        if connect_name == 'ICP_ID' and not result.get('project_id'):
            project = self.env['compassion.project'].create({
                'fcp_id': value
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

    def __init__(self, env):
        super(CompassionChildMapping, self).__init__(env)
        self.CONSTANTS = {'gpid': env.user.country_id.code}

    def _process_odoo_data(self, odoo_data):
        if 'gender' in odoo_data:
            if odoo_data['gender'] == 'Female':
                odoo_data['gender'] = 'F'
            else:
                odoo_data['gender'] = 'M'
        # Replace list of dict by the household id (created or updated)
        if 'household_id' in odoo_data:
            household_data = odoo_data['household_id'][0]
            household = self.env['compassion.household'].search(
                [('household_id', '=', household_data[
                    'household_id'])])
            if household:
                household.write(household_data)
                odoo_data['household_id'] = household.id
            else:
                odoo_data['household_id'] = household.create(household_data).id

        # Unlink old revised values and create new ones
        if isinstance(odoo_data.get('revised_value_ids'), list):
            child = self.env['compassion.child'].search([
                ('global_id', '=', odoo_data['global_id'])])
            child.revised_value_ids.unlink()
            for value in odoo_data['revised_value_ids']:
                self.env['compassion.major.revision'].create({
                    'name': value,
                    'child_id': child.id,
                })
            del odoo_data['revised_value_ids']
