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
    'version': '10.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['crm_claim_code',
                'crm_claim_type',
                'mail',
                'web_widget_text_collapse_html'
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/request_sequence.xml',
        'data/crm_request_data.xml',
        'views/request.xml',
        'views/request_type.xml',
        'views/request_stage.xml',
    ],
}
