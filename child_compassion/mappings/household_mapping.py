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
        "HouseholdName": 'name',
        "NumberOfLinkedBeneficiaries": 'number_beneficiaries',
        "HouseholdId": "household_id",
        "TogetherNow": 'parents_together',
        "IsNaturalFatherAlive": "father_alive",
        "NaturalFatherLivingWithChild": "father_living_with_child",
        "IsNaturalMotherAlive": "mother_alive",
        "NaturalMotherLivingWithChild": "mother_living_with_child",
        "FatherOrMaleGuardianEmplStatus": "male_guardian_job_type",
        "MotherOrFemaleGuardianEmplStatus": "female_guardian_job_type",
        "FatherOrMaleGuardianOcc": "male_guardian_job"
    }


class HouseholdMemberMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.household.member'

    CONNECT_MAPPING = {
        "Role": "role",
        "Name": "FatherCaregiver",
        "IsCaregiver": 'is_caregiver',
        "IsPrimaryCaregiver": 'is_primary_caregiver',
        "CompassionBenefName": ""
    }
