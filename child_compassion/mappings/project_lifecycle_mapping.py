# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>, Philippe Heer
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping


class ICPLifecycleMapping(OnrampMapping):
    ODOO_MODEL = 'compassion.project.ile'
    MAPPING_NAME = "new_project_lifecyle"

    CONNECT_MAPPING = {
        "ActionPlanGPAUse": "action_plan",
        "ActualSuspensionEndDate": "suspension_end_date",
        "ActualTransitionDate": "date",
        "FutureInvolvement": ("future_involvement_ids.name",
                              "fcp.involvement"),
        "ICPImprovementDescription": "fcp_improvement_desc",
        "ICPLifecycleEventType": "type",
        "IsBeneficiaryInformationUpdatesWithheld":
            "is_beneficiary_information_updates_withheld",
        "IsBeneficiaryToSupporterLettersWithheld": "hold_b2s_letters",
        "IsGiftsWithheld": "hold_gifts",
        "IsSponsorshipFundsWithheld": "hold_cdsp_funds",
        "IsSuporterToBeneficiaryLettersWithheld": "hold_s2b_letters",
        "IsSurvivalFundsWithheld": "hold_csp_funds",
        "IsSuspensionExtendedAdditionalThirtyDays": "extension_2",
        "IsSuspensionExtendedThirtyDays": "extension_1",
        "IsTransitionComplete": "transition_complete",
        "Name": "name",
        "ProjectedTransitionDate": "projected_transition_date",
        "ReactivationDate": "reactivation_date",
        "ReasonForFirstExtension": ("extension_1_reason_ids.name",
                                    "fcp.suspension.extension.reason"),
        "ReasonforSecondExtension": ("extension_2_reason_ids.name",
                                     "fcp.suspension.extension.reason"),
        "SuspensionDetailsGPAUse": "suspension_detail",
        "SuspensionReason": ("suspension_reason_ids.name",
                             "fcp.lifecycle.reason"),
        "SuspensionStartDate": "suspension_start_date",
        "TransitionDetailsGPAUse": "details",
        "TransitionReason": ("transition_reason_ids.name",
                             "fcp.lifecycle.reason"),
        "TranslationStatus": "translation_status",
        "ICPStatus": "project_status",
        "ICP_ID": ('project_id.fcp_id', 'compassion.project'),

        # Not used in Odoo
        'SourceKitName': None,
        "TranslationCompletedFields": None,
        "TranslationRequiredFields": None,
    }

    FIELDS_TO_SUBMIT = {
        'gpid': None,
    }

    def __init__(self, env):
        super(ICPLifecycleMapping, self).__init__(env)
        self.CONSTANTS = {'gpid': env.user.country_id.code}

    def _process_odoo_data(self, odoo_data):
        # Convert Project Status
        status = odoo_data.get('project_status')
        if status:
            status_mapping = {
                'Active': 'A',
                'Phase Out': 'P',
                'Suspended': 'S',
                'Transitioned': 'T',
            }
            odoo_data['project_status'] = status_mapping[status]
