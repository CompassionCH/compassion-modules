# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Interaction Resume",
    "summary": "Display a timeline of all communications exchanged with a partner",
    "version": "18.0.1.0.0",
    # see https://odoo-community.org/page/development-status
    "development_status": "Beta",
    "category": "Tools",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "author": "Compassion Switzerland",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "data": [
        "data/base_automation.xml",
        "security/ir.model.access.csv",
        "views/partner_log_other_interaction_wizard_view.xml",
        "views/res_partner_view.xml",
        "views/interaction_resume.xml",
        "views/mail_message_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "interaction_resume/static/src/xml/**/*.xml",
            "interaction_resume/static/src/js/**/*.js",
        ],
    },
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "advanced_translation",
        "partner_communication",
        "crm_claim",
        "crm_phonecall",
        "website",
        "base_automation",
        "mail_tracking",
    ],
}
