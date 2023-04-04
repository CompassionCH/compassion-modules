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
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
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
    "name": "Compassion Interventions",
    "version": "14.0.1.0.0",
    "category": "Compassion",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "sponsorship_compassion",
        "base_automation",
    ],
    "external_dependencies": {},
    "data": [
        "data/compassion.intervention.category.csv",
        "data/compassion.intervention.subcategory.csv",
        "data/compassion.intervention.deliverable.csv",
        "data/install_category_rel.xml",
        "data/intervention_action_rules.xml",
        "data/compassion_mapping.xml",
        "data/gmc_action.xml",
        "security/intervention_groups.xml",
        "security/ir.model.access.csv",
        "views/compassion_intervention_view.xml",
        "views/global_intervention_view.xml",
        "views/intervention_search_view.xml",
        "views/project_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "load_mappings",
}
