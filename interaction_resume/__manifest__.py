# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Interaction Resume",
    "summary": "Display a timeline of all communications exchanged with a partner",
    "version": "14.0.1.0.0",
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
        "static/src/xml/assets.xml",
    ],
    "qweb": [
        "static/src/xml/tree_button.xml",
    ],
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
        "partner_contact_in_several_companies",
        "base_automation",
        "mail_tracking",
    ],
}
