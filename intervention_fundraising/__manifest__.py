##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
{
    "name": "Compassion Intervention Fundraising",
    "summary": "Pledges, funding gap and fundraising dashboard of the interventions",
    "version": "18.0.1.0.0",
    "category": "Compassion",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "intervention_compassion",  # compassion-modules
        "crm",
        "spreadsheet_dashboard",
    ],
    "data": [
        "security/fundraising_groups.xml",
        "security/ir.model.access.csv",
        "data/crm_team.xml",
        "data/intervention_donor_type.xml",
        "views/compassion_intervention_view.xml",
        "views/crm_lead_view.xml",
        "views/intervention_fundraising_report_view.xml",
        "views/intervention_fundraising_line_view.xml",
        "views/intervention_donor_type_view.xml",
        "views/res_config_settings_view.xml",
        "views/menu.xml",
        "data/spreadsheet_dashboard.xml",
    ],
    "installable": True,
}
