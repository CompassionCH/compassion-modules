# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Partner Documents Folder",
    "summary": "External documents folder (e.g. Google Drive) on partners, "
    "filed by salesperson",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Partner Management",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": ["fs_folder", "queue_job"],
    "data": ["views/res_partner_views.xml"],
    "installable": True,
}
