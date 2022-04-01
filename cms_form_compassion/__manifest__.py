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
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
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
    "name": "CMS Form additions for Compassion",
    "version": "12.0.1.0.2",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules/tree/10.0",
    "depends": [
        "cms_form",  # oca_addons/website_cms
        "website_payment",  # source/addons
        "account_payment",  # source/addons
        "portal",  # source/addons
        "queue_job",  # oca_addons/queue
        "base_automation",  # source/addons
        "link_tracker",  # source/addons
        "base_location"  # oca_addons/partner-contact
    ],
    "data": [
        "data/ir.config_parameter.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "templates/assets.xml",
        "templates/form_widgets.xml",
        "templates/payment_templates.xml",
        "views/config_view.xml",
        "views/ir_logging.xml",
        "data/activity_data.xml",
        "data/base_automation_data.xml"
    ],
    "demo": [],
    "development_status": "Stable",
    "installable": True,
    "auto_install": False,
}
