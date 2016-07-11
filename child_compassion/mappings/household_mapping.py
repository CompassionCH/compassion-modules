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
        "BeneficiaryHouseholdMemberDetails": ('member_ids',
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
        'RevisedValues': 'revised_value_ids',

        # Not define
        "SourceKitName": None,
    }

    def _process_odoo_data(self, odoo_data):
        # Replace dict by a tuple for the ORM update/create
        if 'member_ids' in odoo_data:
            # Remove all members
            household = self.env[self.ODOO_MODEL].search(
                [('household_id', '=', odoo_data['household_id'])])
            household.member_ids.unlink()

            member_list = list()
            for member in odoo_data['member_ids']:
                orm_tuple = (0, 0, member)
                member_list.append(orm_tuple)
            odoo_data['member_ids'] = member_list or False

        # Unlink old revised values and create new ones
        if 'revised_value_ids' in odoo_data:
            household = self.env[self.ODOO_MODEL].search(
                [('household_id', '=', odoo_data['household_id'])])
            household.revised_value_ids.unlink()
            for value in odoo_data['revised_value_ids']:
                self.env['compassion.major.revision'].create({
                    'name': value,
                    'household_id': household.id,
                })
            del odoo_data['revised_value_ids']


class HouseholdMemberMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.household.member'

    CONNECT_MAPPING = {
        "Beneficiary_GlobalID": ('child_id.global_id', 'compassion.child'),
        "Beneficiary_LocalID": ('child_id.local_id', 'compassion.child'),
        "FullName": None,
        "HouseholdMemberRole": 'role',
        "HouseholdMember_Name": 'name',
        "IsCaregiver": 'is_caregiver',
        "IsPrimaryCaregiver": 'is_primary_caregiver',
    }
