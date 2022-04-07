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
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
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
    "name": "Compassion CH - Events",
    "version": "12.0.1.0.1",
    "category": "CRM",
    "sequence": 150,
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "base_location",  # oca_addons/partner_contact
        "sponsorship_compassion",  # compassion-modules
        "partner_communication",  # compassion-modules
        "mail_tracking",  # oca_addons/social
        "partner_contact_in_several_companies",  # oca_addons/partner-contact
        "mass_mailing",
        "base_automation",
    ],
    "data": [
        "data/account_analytic_data.xml",
        "data/calendar_event_type.xml",
        "data/demand_planning.xml",
        "security/crm_compassion_security.xml",
        "security/ir.model.access.csv",
        "static/src/xml/assets.xml",
        "views/account_invoice_line.xml",
        "views/calendar_event_view.xml",
        "views/calendar_view.xml",
        "views/contract_origin_view.xml",
        "views/crm_claim_menu.xml",
        "views/crm_lead_view.xml",
        "views/demand_planning_settings.xml",
        "views/demand_planning.xml",
        "views/demand_weekly_revision.xml",
        "views/event_compassion_view.xml",
        "views/field_view.xml",
        "views/global_childpool_view.xml",
        "views/hold_view.xml",
        "views/interaction_resume_view.xml",
        "views/mail_message_view.xml",
        "views/partner_log_interaction_wizard_view.xml",
        "views/partner_log_other_interaction_wizard_view.xml",
        "views/res_partner_view.xml",
        "views/sponsorship_view.xml",
    ],
    "qweb": [
        "static/src/xml/kanban_colors.xml"
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
