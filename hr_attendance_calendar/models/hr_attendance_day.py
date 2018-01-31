# -*- coding: utf-8 -*-
# (C) 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import datetime


class HrDayAttendance(models.Model):
    _name = "hr.attendance.day"
    _order = 'name DESC'

    name = fields.Date(string="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    attendance_ids = fields.One2many('hr.attendance', string="Attendances",
                                     compute='_get_attendances')
    calendar_att_ids = fields.One2many('resource.calendar.attendance',
                                       string="Working schedule",
                                       compute='_get_calendar_att')
    calendar_worked_hours = fields.Float(string='Logged hours (based on '
                                                'calendar)',
                                         compute='_get_worked_hours',
                                         store=True,
                                         readonly=False)
    calendar_due_hours = fields.Float(string="Due hours (based on calendar)",
                                      compute='_get_due_hours')
    total_break_hours = fields.Float(string="Total break",
                                     compute='_get_total_break_time')
    total_calendar_breaks = fields.Float(string="Total break (calendar)",
                                         compute='_get_total_calendar_'
                                                 'break_time')
    total_bonus_malus = fields.Float(string="Bonus/Malus",
                                     compute='_compute_get_bonus_malus')

    @api.multi
    def _compute_get_bonus_malus(self):
        for att_day in self:
            att_day.total_bonus_malus = att_day.calendar_worked_hours - \
                                        att_day.calendar_due_hours

    @api.multi
    def _get_due_hours(self):
        for att_day in self:
            due_hours = 0
            for att_cal in att_day.calendar_att_ids:
                due_hours += att_cal.due_hours
            att_day.calendar_due_hours = due_hours
            public_holidays = self.env['hr.holidays.public.line'].search([
                ('date', '=', att_day.name)
            ])
            att_day_date = fields.Date.from_string(att_day.name)
            holidays = self.env['hr.holidays'].search([
                ('holiday_status_id.limit', '=', False),
                ('employee_id', '=', att_day.employee_id.id),
                ('date_from', '<=',
                 datetime.strftime(att_day_date, "%Y-%m-%d 12:00:00")),
                ('date_to', '>=',
                 datetime.strftime(att_day_date, "%Y-%m-%d 12:00:00")),
            ])
            if public_holidays:
                att_day.calendar_due_hours = 0
            else:
                if due_hours == 0 and not holidays:
                    for working_hour in \
                        att_day.employee_id.contract_id.working_hours \
                            .attendance_ids:
                        if working_hour.dayofweek == str(
                            fields.Date.from_string(att_day.name).weekday()):
                            due_hours += working_hour.due_hours

                    att_day.calendar_due_hours = due_hours

    @api.multi
    def _get_calendar_att(self):
        for att_day in self:
            att_calendar_ids = []
            for att in att_day.attendance_ids:
                for att_cal in att.calendar_att_ids:
                    att_calendar_ids.append(att_cal.id)
            att_day.calendar_att_ids = att_calendar_ids

    @api.multi
    def _get_total_calendar_break_time(self):
        for att_day in self:
            total_calendar_breaks = 0
            for call_att in att_day.calendar_att_ids:
                total_calendar_breaks += call_att.break_hours
            att_day.total_calendar_breaks = total_calendar_breaks

    @api.multi
    def _get_total_break_time(self):
        for att_day in self:
            sorted_attendances = sorted(att_day.attendance_ids,
                                        key=lambda att: att.check_in)
            last_checkout = False
            total_break_hours = 0
            for att in sorted_attendances:
                if last_checkout:
                    check_in = fields.Datetime.from_string(att.check_in)
                    check_out = fields.Datetime.from_string(last_checkout)
                    break_time = int((check_in - check_out).seconds / 3600) + (
                        ((check_in - check_out).seconds / 60) % 60) / 60.0
                    total_break_hours += break_time
                last_checkout = att.check_out
            att_day.total_break_hours = total_break_hours

    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _get_worked_hours(self):
        for att_day in self:
            worked_hours = 0
            for attendance in att_day.attendance_ids:
                worked_hours += attendance.calendar_worked_hours
            att_day.calendar_worked_hours = worked_hours
            if att_day.total_calendar_breaks > att_day.total_break_hours:
                att_day.calendar_worked_hours += (
                    att_day.total_break_hours - att_day.total_calendar_breaks)

    @api.multi
    def _get_attendances(self):
        for att_day in self:
            att_ids = []
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', att_day.employee_id.id)
            ])
            for attendance in attendances:
                att_check_in_date = fields.Date.from_string(
                    attendance.check_in)
                att_check_out_date = fields.Date.from_string(
                    attendance.check_out)
                att_day_date = fields.Date.from_string(att_day.name)
                if att_day_date == att_check_in_date or att_day_date == \
                    att_check_out_date:
                    att_ids.append(attendance.id)
            if att_ids:
                att_day.attendance_ids = att_ids
