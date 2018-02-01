# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)

class CreateHrAttendance(models.TransientModel):
    _name = 'create.hr.attendance.day'

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")
    employee_id = fields.Many2one('hr.employee', string='Employee')

    def create_attendance_day(self):
        date_to = fields.Date.from_string(self.date_to)
        date_from = fields.Date.from_string(self.date_from)

        current_date = date_from
        att_day = self.env['hr.attendance.day']

        while (current_date <= date_to):
            already_exist = att_day.search([
                ('employee_id', '=', self.employee_id.id),
                ('name', '=', current_date)
            ])
            _logger.info("CREATE")
            if not already_exist:

                att_day.create({
                    'employee_id': self.employee_id.id,
                    'name': current_date,
                })
            _logger.info(current_date)
            _logger.info(date_to)
            current_date = current_date + timedelta(days=1)