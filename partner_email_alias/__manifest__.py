# Copyright 2023 CompassionCH (https://www.compassion.ch/)
# @author: Emanuel Cino <ecino@compassion.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Partner Email Aliases",
    "summary": "Add many e-mail addresses on a contact",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Partner Management",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "author": "Compassion Switzerland",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["mail"],
    "data": [
        "views/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
}
