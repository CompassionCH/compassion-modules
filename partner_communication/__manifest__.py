##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# pylint: disable=C8101
{
    "name": "Partner Communication",
    "version": "14.0.1.0.1",
    "category": "Other",
    "author": "Compassion Switzerland",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "base_report_to_printer",  # OCA/report-print-send
        "contacts",
        "queue_job",  # OCA/queue
        "utm",
    ],
    "external_dependencies": {"python": ["wand"]},
    "data": [
        "security/ir.model.access.csv",
        "security/communication_job_security.xml",
        "report/a4_communication.xml",
        "views/communication_job_view.xml",
        "views/communication_config_view.xml",
        "views/res_partner_view.xml",
        "views/change_text_wizard_view.xml",
        "views/pdf_wizard_view.xml",
        "views/generate_communication_wizard_view.xml",
        "views/ir_attachment_view.xml",
        "views/ir_actions_view.xml",
        "views/download_print_wizard_view.xml",
        "views/settings_view.xml",
        "views/communication_snippet_view.xml",
        "views/mail_template_views.xml",
        "data/default_communication.xml",
        "data/queue_job.xml",
    ],
    "qweb": [],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
    "auto_install": False,
}
