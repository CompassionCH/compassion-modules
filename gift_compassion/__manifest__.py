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
    "name": "Compassion Sponsorship Gifts",
    "version": "14.0.1.0.2",
    "category": "Compassion",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": ["sponsorship_compassion"],
    "data": [
        "security/ir.model.access.csv",
        "data/gift_thresholds.xml",
        "data/process_gift_cron.xml",
        "views/collect_gifts_wizard_view.xml",
        "views/gift_view.xml",
        "views/settings_view.xml",
        "views/contracts_view.xml",
        "views/account_move_view.xml",
        "data/gift_compassion_mapping.xml",
        "data/gmc_action.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "load_mappings",
}

# pylint: disable=C8101
