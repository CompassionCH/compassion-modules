# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Attendance - Calendar',
    'summary': 'Compute extra hours based on attendances',
    'category': 'Human Resources',
    'author': "CompassionCH, Open Net Sàrl",
    'depends': [
        'hr',
        'hr_employee',
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
        'views/hr_attendance_view.xml',
        'views/hr_employee.xml',
        'views/hr_holidays_status_views.xml',
        'wizard/create_hr_attendance_day_view.xml',
        'data/attendance_computation_cron.xml'
    ],
    'installable': True
}
