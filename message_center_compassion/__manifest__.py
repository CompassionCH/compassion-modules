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
#    Copyright (C) 2014-2019 Compassion CH (http://www.compassion.ch)
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
    "name": "Compassion CH Message Center",
    "version": "14.0.1.0.1",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "development_status": "Stable",
    "depends": ["base", "queue_job"],
    "external_dependencies": {"python": ["jwt"], },
    "data": [
        "security/gmc_groups.xml",
        "security/ir.model.access.csv",
        "data/query_operators.xml",
        "views/gmc_message_view.xml",
        "views/advanced_query_view.xml",
        "views/compassion_mapping_view.xml",
        "views/import_json_mapping_view.xml",
        "views/compassion_settings_view.xml",
        "data/queue_job.xml",
    ],
    "demo": ["demo/res_users.xml"],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "load_mappings",
}
