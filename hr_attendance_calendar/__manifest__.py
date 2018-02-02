# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Attendance - Calendar',
    'summary': 'Compute Bonus/Malus based on attendances',
    'description': 'Compute Bonus/Malus based on attendances',
    'category': 'Human Resources',
    'author': "Open Net Sàrl",
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_public_holidays'
    ],
    'version': '9.0.1.0.0',
    'auto_install': False,
    'website': 'http://open-net.ch',
    'license': 'AGPL-3',
    'images': [],
    'data': [
        'security/ir.model.access.csv',
        # 'security/hr_security.xml',
        'views/hr_attendance_calendar_view.xml',
        # 'views/resource_calendar_view.xml',
        # 'views/hr_holidays.xml',
        'views/hr_employee.xml',
        'views/hr_attendance_view.xml',
        'wizard/create_hr_attendance_day_view.xml',
        'data/attendance_computation_cron.xml'
    ],
    'installable': True
}
