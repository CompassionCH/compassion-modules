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
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
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
    "name": "Compassion Sponsorships",
    "version": "14.0.1.0.0",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "recurring_contract",  # compassion-accounting
        "utm",
        "crm",
        "child_compassion",
        "web_m2x_options",  # oca/web
        "partner_firstname",  # oca/partner-contact
        "account_analytic_attribution",  # compassion-accounting
    ],
    "data": [
        "views/sponsorship_contract_view.xml",
        "views/invoice_line_view.xml",
        "views/res_partner_view.xml",
        "views/privacy_statement.xml",
        "views/generate_gift_view.xml",
        "views/account_invoice_split_wizard_view.xml",
        "views/child_view.xml",
        "views/contracts_report_view.xml",
        "views/gmc_message_view.xml",
        "views/end_contract_wizard_view.xml",
        "views/download_child_pictures_view.xml",
        "views/project_view.xml",
        "views/activate_contract_view.xml",
        "views/contract_group_view.xml",
        "views/contract_origin_view.xml",
        "views/project_view.xml",
        "views/utm_medium_view.xml",
        "data/compassion_mapping.xml",
        "data/sponsorship_product.xml",
        "data/gmc_action.xml",
        "data/end_reasons.xml",
        "data/partner_category_data.xml",
        "data/utm_data.xml",
        "data/res_partner_sequence.xml",
        "data/queue_job.xml",
        "security/ir.model.access.csv",
        "views/product_views.xml",
    ],
    "demo": ["demo/demo_data.xml", ],
    "installable": True,
    "auto_install": False,
    "development_status": "Stable",
    "post_init_hook": "load_mappings",
}
