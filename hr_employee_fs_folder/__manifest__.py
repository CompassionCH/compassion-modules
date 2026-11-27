# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Employee Documents Folder",
    "summary": "External documents folder (e.g. Google Drive) per employee, "
    "with a subfolder shared read-only with the employee",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": ["hr", "fs_folder", "queue_job"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/hr_employee_views.xml",
        "views/hr_employee_shared_folder_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_employee_fs_folder/static/src/fs_folder_readonly.esm.js",
            "hr_employee_fs_folder/static/src/fs_folder_readonly.xml",
        ],
    },
    "installable": True,
}
