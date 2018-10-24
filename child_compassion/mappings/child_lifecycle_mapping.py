# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class LifecycleMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.child.ble'
    MAPPING_NAME = 'new_child_lifecyle'

    CONNECT_MAPPING = {
        'DateOfDeath': 'child_death_date',
        'DeathCategory': 'child_death_category',
        'DeathSubcategory': 'child_death_subcategory',
        'FamilyImpact': 'family_impact',
        'FutureHopes': ('future_hope_ids.name', 'child.future.hope'),
        'IsFinalLetterSent': 'final_letter_sent',
        'IsPrimarySchoolComplete': 'primary_school_finished',
        'LastAttendedDate': 'last_attended_project',
        'NewSituation': 'new_situation',
        'SponsorImpact': 'sponsor_impact',
        'CurrentFCP': 'current_project',
        'Status': 'status',
        'DeathInterventionInformation': 'death_intervention_information',
        'EffectiveDate': 'date',
        'BeneficiaryLifecycleEvent_ID': 'global_id',
        'ReasonForRequest': 'request_reason',
        'ExpectedArrivalDate': 'transfer_arrival_date',
        'NewBeneficiaryLocalNumber': ('child_id.local_id', 'compassion.child'),
        'NewFCPID': 'new_project',
        'OtherReasonForTransfer': 'other_transfer_reason',
        'BeneficiaryTransitionType': 'transition_type',
        'NewProgram': 'new_program',
        'PreviouslyActiveProgram': 'previously_active_program',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        'RecordType': 'type',

        # Not used in Odoo
        'Beneficiary_LocalID': None,
        'BeneficiaryStatus': None,
        'NewFCPName': None,
        'SourceKitName': None,
    }

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    def __init__(self, env):
        super(LifecycleMapping, self).__init__(env)
        self.CONSTANTS = {'gpid': env.user.country_id.code}

    def _process_odoo_data(self, odoo_data):
        """ Put the request reason in lower case. """
        request_reason = odoo_data.get('request_reason')
        if request_reason:
            odoo_data['request_reason'] = request_reason.lower()

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Convert Future Hopes in List"""
        if connect_name == 'FutureHopes' and value:
            value = value.split(';')
        return super(LifecycleMapping, self)._convert_connect_data(
            connect_name, value_mapping, value, relation_search
        )
