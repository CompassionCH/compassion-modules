# -*- coding: utf-8 -*-
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    'name': "crm_request",

    'author': "Compassion CH",
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',

    'category': 'CRM',
    'version': '10.0.1.2.0',

    # Python dependencies
    'external_dependencies': {
        'python': ['detectlanguage']
    },

    # any module necessary for this one to work correctly
    'depends': ['crm_claim_code',
                'crm_claim_type',
                'mail',
                'partner_contact_in_several_companies',
                'advanced_translation',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/request_sequence.xml',
        'data/crm_request_data.xml',
        'data/holiday_closure_email_template.xml',
        'views/request.xml',
        'views/request_type.xml',
        'views/holiday_automated_response_view.xml',
        'views/request_stage.xml',
        'security/ir.model.access.csv',
    ],
}
