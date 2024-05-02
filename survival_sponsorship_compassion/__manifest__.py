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
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester, Emanuel Cino
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
    "name": "Compassion Survival Sponsorships",
    "version": "14.0.1.0.0",
    "summary": "New type for the sponsorships that add the possibility "
    "to sponsor a country in the survival program (CSP).",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "sponsorship_compassion",  # compassion-modules
        "intervention_compassion",  # compassion-modules
    ],
    "data": [
        "views/product_product_view.xml",
        "views/product_template_view.xml",
        "views/recurring_contract.xml",
        "views/res_config_settings_view.xml",
        "data/product_warning_automation.xml",
        "data/survival_product_template.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "development_status": "Production/Stable",
}
