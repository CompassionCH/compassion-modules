# -*- coding: utf-8 -*-
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
    'name': 'Compassion CH - Events',
    'version': '10.0.1.4.0',
    'category': 'CRM',
    'sequence': 150,
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'base_location',
        'sponsorship_compassion',
        'partner_communication',
        'project',
        'crm_request',
        'mail_tracking',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/crm_compassion_security.xml',
        'data/account_analytic_data.xml',
        'data/calendar_event_type.xml',
        'data/demand_planning_server_actions.xml',
        'data/demand_planning_action_rules.xml',
        'views/event_compassion_view.xml',
        'views/contract_origin_view.xml',
        'views/crm_lead_view.xml',
        'views/project_view.xml',
        'views/account_invoice_line.xml',
        'views/interaction_resume_view.xml',
        'views/res_partner_view.xml',
        'views/calendar_event_view.xml',
        'views/demand_planning.xml',
        'views/demand_weekly_revision.xml',
        'views/hold_view.xml',
        'views/calendar_view.xml',
        'views/mail_message_view.xml',
        'views/partner_log_interaction_wizard_view.xml',
    ],
    'qweb': [
        'static/src/xml/web_fullcalendar_event.xml',
    ],
    'demo': [],
    'installable': False,
    'auto_install': False,
}
