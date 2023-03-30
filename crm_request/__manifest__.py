# Copyright 2018-2023 CompassionCH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CRM Request",
    "summary": "Enables Customer Support Inbox",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Helpdesk",
    "website": "https://www.compassion.ch",
    "author": "Compassion CH",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {
        'python': [
            'pandas>=1.5.3'
        ]
    },
    "depends": [
        "mail",
        "advanced_translation",
        "hr_holidays",
        "crm_claim_code",  # oca_addons/crm
        "mail_quoted_reply",  # OCA/social
        "partner_auto_match",
        "partner_email_alias",
        "partner_salutation",
        "partner_communication",
    ],
    "data": [
        "data/request_email_template.xml",
        "data/crm_request_data.xml",
        "data/request_sequence.xml",
        "data/ir_cron.xml",
        "views/request.xml",
        "views/request_category.xml",
        "views/holiday_automated_response_view.xml",
        "security/ir.model.access.csv",
    ],
}
