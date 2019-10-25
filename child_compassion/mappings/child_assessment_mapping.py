# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.message_center_compassion.mappings.base_mapping import \
    OnrampMapping
from datetime import datetime


class ChildAssessmentMapping(OnrampMapping):
    """
    Child Assessment Mapping
    """
    ODOO_MODEL = 'compassion.child.cdpr'
    MAPPING_NAME = 'beneficiary_cdpr'

    CONNECT_MAPPING = {
        'AssesmentType': 'assesment_type',
        'CognitiveOutcomeScore': 'cognitive_score',
        'CompletionDate': 'date',
        'PhysicalOutcomeScore': 'physical_score',
        'SocioEmotionalOutcomeScore': 'sociological_score',
        'SpiritualOutcomeScore': 'spiritual_score',
        'Age': 'age',
        'Beneficiary_GlobalID': ('child_id.global_id', 'compassion.child'),
        'CDPRAgeGroup': 'cdpr_age_group',
        'SourceKitName': 'source_kit_name',
    }

    def _process_connect_data(self, connect_data):
        # Set end date to correct format for Connect
        if 'CompletionDate' in connect_data:
            end_date_str = connect_data.get('CompletionDate')
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
            connect_data['CompletionDate'] = end_date.strftime(
                "%Y-%m-%dT%H:%M:%SZ")
