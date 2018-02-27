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
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.com>
#    @author: David Coninckx <david@coninckx.com>
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
    'name': 'Attendance - Calendar',
    'summary': 'Compute extra hours based on attendances',
    'category': 'Human Resources',
    'author': "CompassionCH, Open Net Sàrl",
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_public_holidays'
    ],
    'version': '10.0.1.0.0',
    'auto_install': False,
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'images': [],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_calendar_view.xml',
        'views/hr_attendance_day_view.xml',
        'views/hr_attendance_settings.xml',
        'views/hr_attendance_view.xml',
        'views/hr_employee.xml',
        'views/hr_holidays_status_views.xml',
        'views/attendance.xml',
        'data/attendance_computation_cron.xml'
    ],
    'installable': True,
    'qweb': [
        "static/src/xml/attendance.xml",
    ],
}
