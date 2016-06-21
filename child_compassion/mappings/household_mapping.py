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


class HouseHoldMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.household'

    CONNECT_MAPPING = {
        "BeneficiaryHouseholdMemberList": ('member_ids',
                                           'compassion.household.member'),
        "FemaleGuardianEmploymentStatus": 'female_guardian_job_type',
        "FemaleGuardianOccupation": 'female_guardian_job',
        "Household_ID": "household_id",
        "Household_Name": "name",
        "IsNaturalFatherLivingWithChild": 'father_living_with_child',
        "IsNaturalMotherLivingWithChild": 'mother_living_with_child',
        "MaleGuardianEmploymentStatus": 'male_guardian_job_type',
        "MaleGuardianOccupation": "male_guardian_job",
        "NaturalFatherAlive": "father_alive",
        "NaturalMotherAlive": "mother_alive",
        "NumberOfSiblingBeneficiaries": "number_beneficiaries",
        "ParentsMaritalStatus": "marital_status",
        "ParentsTogether": "parents_together",
        "SourceKitName": "HouseholdKit",
    }


class HouseholdMemberMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.household.member'

    CONNECT_MAPPING = {
        "Beneficiary_GlobalID": 'beneficiary_global_id',
        "Beneficiary_LocalID": 'beneficiary_local_id',
        "FullName": None,
        "HouseholdMemberRole": 'role',
        "HouseholdMember_Name": 'name',
        "IsCaregiver": 'is_caregiver',
        "IsPrimaryCaregiver": 'is_primary_caregiver',
    }
