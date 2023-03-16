# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "crm_request",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "category": "CRM",
    "version": "14.0.0.0.0",
    # Python dependencies
    'external_dependencies': {
        'python': [
            'pandas>=1.5.3'
        ]
    },
    # any module necessary for this one to work correctly
    "depends": [
        "crm_claim_code",  # oca_addons/crm
        "mail",
        "partner_contact_in_several_companies",  # oca_addons/partner-contact
        "advanced_translation",
        "cms_form_compassion",
    ],
    # always loaded
    "data": [
        "data/request_email_template.xml",
        "data/crm_request_data.xml",
        "data/ignored_reporter.xml",
        "data/request_sequence.xml",
        "data/ir_cron.xml",
        "views/request.xml",
        "views/request_category.xml",
        "views/holiday_automated_response_view.xml",
        "views/request_stage.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
