# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta

from odoo import models, fields, api


class HrAttendanceSettings(models.TransientModel):
    """ Settings configuration for hr.attendance."""
    # _name = "hr.attendance.settings"
    _inherit = 'base.config.settings'

    work_day_duration = fields.Float('Workday duration (hour)',
                                     help='For the calculation of the half '
                                          'day in the calculation of the '
                                          'holidays')
    free_break = fields.Float('Free break (hour)')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def set_work_day_duration(self):
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_calendar.work_day_duration',
            str(self.work_day_duration))

    @api.multi
    def set_free_break(self):
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_calendar.free_break',
            str(self.free_break))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        res = {
            'work_day_duration': float(param_obj.get_param(
                'hr_attendance_calendar.work_day_duration', '8.0')),
            'free_break': float(param_obj.get_param(
                'hr_attendance_calendar.free_break', '0.0'))
        }
        return res

    @api.model
    def get_work_day_duration(self):
        return float(self.env['ir.config_parameter'].get_param(
            'hr_attendance_calendar.work_day_duration'))

    @api.model
    def get_free_break(self):
        return float(self.env['ir.config_parameter'].get_param(
            'hr_attendance_calendar.free_break'))


class CreateHrAttendance(models.TransientModel):
    _name = 'create.hr.attendance.day'

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")
    employee_ids = fields.Many2many('hr.employee', string='Employee')

    def create_attendance_day(self):
        date_to = fields.Date.from_string(self.date_to)
        current_date = fields.Date.from_string(self.date_from)

        att_day = self.env['hr.attendance.day']

        for employee_id in self.employee_ids:
            while current_date <= date_to:
                already_exist = att_day.search([
                    ('employee_id', '=', employee_id.id),
                    ('date', '=', current_date)
                ])
                if not already_exist:

                    att_day.create({
                        'employee_id': employee_id.id,
                        'date': current_date,
                    })
                current_date = current_date + timedelta(days=1)
