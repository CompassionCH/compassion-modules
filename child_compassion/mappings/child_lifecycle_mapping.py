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


class ICPMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.child.ble'
    MAPPING_NAME = "new_child_lifecyle"

    CONNECT_MAPPING = {
        'DateOfDeath': 'child_death_date',
        'DeathCategory': 'child_death_category',
        'DeathSubcategory': 'child_death_subcategory',
        'FamilyImpact': 'family_impact',
        'FutureHopes': 'future_hopes',
        'IsFinalLetterSent': 'final_letter_sent',
        'IsPrimarySchoolComplete': 'primary_school_finished',
        'LastAttendedDate': 'last_attended_project',
        'NewSituation': 'new_situation',
        'SponsorImpact': 'sponsor_impact',
        'CurrentICP': None,
        'Status': 'Cancelled',
        'DeathInterventionInformation': None,
        'EffectiveDate': 'date',
        'BeneficiaryLifecycleEvent_ID': None,
        'ReasonForRequest': 'request_reason',
        'RecordType': 'Planned Exit',
        'ExpectedArrivalDate': None,
        'NewBeneficiaryLocalNumber': ('child_id.local_id', 'compassion.child'),
        'NewICPID': None,
        'OtherReasonForTransfer': 'other_transfer_reason',
        'BeneficiaryTransitionType': 'transition_type',
        'NewProgram': None,
        'PreviouslyActiveProgram': None,
        'BeneficiaryStatus': None,
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        'Beneficiary_LocalID': ('child_id.local_id', 'compassion.child'),

        # Not used in Odoo
        'NewICPName': None,
    }

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    CONSTANTS = {
        'SourceKitName': 'BeneficiaryLifecycleEventKit',
        'BeneficiaryStatus': 'Active',
    }
