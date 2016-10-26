# -*- encoding: utf-8 -*-
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

{
    'name': 'Compassion CH - Events',
    'version': '8.0.3',
    'category': 'CRM',
    'sequence': 150,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['mail', 'base_location', 'sponsorship_compassion', 'project',
                'hr_timesheet', 'hr_expense', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_analytic_data.xml',
        'data/calendar_event_type.xml',
        'data/gmc_action.xml',
        'data/demand_planning_cron.xml',
        'views/event_compassion_view.xml',
        'views/contract_origin_view.xml',
        'views/crm_lead_view.xml',
        'views/project_view.xml',
        'views/hr_timesheet_view.xml',
        'views/account_view.xml',
        'views/close_old_projects_view.xml',
        'views/account_invoice_line.xml',
        'views/res_partner_view.xml',
        'views/calendar_event_view.xml',
        'views/demand_planning.xml',
        'views/demand_weekly_revision.xml',
        'views/hold_view.xml',
        'views/web_calendar_js_loader.xml'
    ],
    'qweb': [
        'static/src/xml/web_fullcalendar_event.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
