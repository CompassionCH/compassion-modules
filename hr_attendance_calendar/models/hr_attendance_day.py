# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Open Net Sarl (https://www.open-net.ch)
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date

from odoo import models, fields, api


class HrDayAttendance(models.Model):
    """
    The instances of hr.attendance.day is created either at the first
    attendance of the day or by the method
    hr.employee._cron_create_attendance() called by a cron everyday.
    """
    _name = "hr.attendance.day"
    _order = 'date DESC'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    date = fields.Date(string="Date",
                       oldname='name',
                       # readonly=True, todo: uncomment
                       required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string="Employee",
                                  ondelete="cascade",
                                  required=True)

    # Working schedule
    cal_att_ids = fields.Many2many(comodel_name='resource.calendar.attendance',
                                   string="Working schedule",
                                   required=True)
    working_day = fields.Char(string="Working day",
                              compute='_compute_working_day',
                              readonly=True,
                              store=True)

    # Leaves
    leave_ids = fields.Many2many(comodel_name='hr.holidays',
                                 string='Leaves')
    in_leave = fields.Boolean(string='In leave',
                              compute='_compute_in_leave',
                              store=True)

    # Due hours
    due_hours = fields.Float(string='Due hours',
                             compute='_compute_due_hours',
                             readonly=True,
                             store=True)

    # Attendances
    attendance_ids = fields.One2many(string="Attendances",
                                     comodel_name='hr.attendance',
                                     inverse_name='attendance_day_id',
                                     readonly=True)

    # Worked
    worked_hours = fields.Float(string='Worked hours',
                                compute='_compute_worked_hours',
                                store=True,
                                readonly=True,
                                oldname='calendar_worked_hours')
    logged_hours = fields.Float(string='Logged hours',
                                compute='_compute_logged_hours',
                                store=True,
                                readonly=True)

    # Break
    # due_break_min = fields.Float(string='Minimum break due',
    #                              compute='_compute_due_break',
    #                              store=True, )
    # due_break_total = fields.Float(string='Total break due',
    #                                compute='_compute_due_break',
    #                                store=True, )
    break_ids = fields.One2many(string='Breaks',
                                comodel_name='hr.attendance.break',
                                inverse_name='attendance_day_id',
                                readonly=True,
                                store=True)
    break_max = fields.Float(string='Longest break',
                             compute='_compute_break_max',
                             store=True, )
    break_total = fields.Float(string='Total break',
                               compute='_compute_break_total',
                               store=True, )

    # Extra hours
    extra_hours = fields.Float(string="Extra hours",
                               compute='_compute_extra_hours',
                               store=True,
                               oldname='total_bonus_malus')
    weighting = fields.Float(String="Weighting",
                             readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('cal_att_ids')
    def _compute_working_day(self):
        for att_day in self.filtered('cal_att_ids'):
            day_id = int(self.cal_att_ids[0].dayofweek)
            days_list = ('Monday',
                         'Tuesday',
                         'Wednesday',
                         'Thursday',
                         'Friday',
                         'Saturday',
                         'Sunday')
            att_day.working_day = days_list[day_id]

    @api.multi
    @api.depends('leave_ids')
    def _compute_in_leave(self):
        for att_day in self:
            if att_day.leave_ids:
                att_day.in_leave = True

    @api.multi
    @api.depends('cal_att_ids', 'leave_ids.state')
    def _compute_due_hours(self):
        for att_day in self:
            due_hours = 0
            for cal_att in att_day.cal_att_ids:
                due_hours += cal_att.due_hours

            if att_day.leave_ids:
                for leave in att_day.leave_ids:
                    if leave.state not in ['validate', 'validate1']:
                        continue
                    if not leave.holiday_status_id.remove_from_due_hours:
                        # todo: use config instead of 8.0
                        due_hours -= leave.compute_work_day(
                            att_day.date) * 8

            att_day.due_hours = due_hours

    @api.multi
    @api.depends('attendance_ids.worked_hours')
    def _compute_worked_hours(self):
        for att_day in self.filtered('attendance_ids'):
            total_hours = 0
            for attendance in att_day.attendance_ids:
                total_hours += attendance.worked_hours
            att_day.worked_hours = total_hours

    @api.multi
    @api.depends('worked_hours')
    def _compute_logged_hours(self):
        # todo: at verify if it's still useful
        pass

    # @api.multi
    # @api.depends('break_ids')
    # def _compute_due_break(self):
    #     for att_day in self:
    #         more_hours = att_day.worked_hours > att_day.due_hours
    #         hours = att_day.worked_hours if more_hours else att_day.due_hours
    #         # todo: verify
    #         rule = self.env['hr.attendance.rules'].search([
    #             ('threshold', '>', hours),
    #         ])
    #         if rule:
    #             att_day.due_break_min = rule[0].due_break
    #             att_day.due_break_total = rule[0].due_break_total
    #         else:
    #             att_day.due_break_min = 0
    #             att_day.due_break_total = 0

    @api.multi
    @api.depends('break_ids')
    def _compute_break_max(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_max = max(att_day.break_ids.mapped('duration'))

    @api.multi
    @api.depends('break_ids')
    def _compute_break_total(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_max = sum(att_day.break_ids.mapped('duration'))

    @api.multi
    @api.depends('worked_hours', 'due_hours')
    def _compute_extra_hours(self):
        for att_day in self.filtered('worked_hours'):
            att_day.extra_hours = att_day.worked_hours - att_day.due_hours

    @api.multi
    def _compute_weighting(self):
        return 1

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create(self, vals):
        rd = super(HrDayAttendance, self).create(vals)

        cal_att_date = fields.Date.from_string(rd.date)

        # link to schedule (resource.calendar.attendance)
        att_day = cal_att_date.weekday()
        cal_att_ids = rd.employee_id.contract_id.working_hours.attendance_ids
        current_cal_att = cal_att_ids.filtered(
            lambda a: int(a.dayofweek) == att_day)

        for cal_att_id in current_cal_att:
            start = cal_att_id.date_from
            start = start if start else date.min
            end = cal_att_id.date_to
            end = end if end else date.max
            if start <= cal_att_date <= end:
                rd.cal_att_ids += cal_att_id

        # link to leaves (hr.holidays )
        holiday_ids = self.env['hr.holidays'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('type', '=', 'remove')])
        for leave in holiday_ids:
            start = fields.Date.from_string(leave.date_from)
            end = fields.Date.from_string(leave.date_to)
            if start <= cal_att_date <= end:
                rd.leave_ids += leave

        # find weighting hours
        weighting = self.env['hr.attendance.weighting'].search([
            ('day_of_week', '=', att_day),
        ])
        # todo: after settings remove
        if not weighting:
            rd.weighting = 1
        else:
            for category in weighting.category_ids:
                if category in rd.category_ids:
                    rd.weighting = weighting
                    break

        # find related attendance
        rd.recompute_attendance()

        # compute breaks
        self.compute_breaks()

        return rd

    @api.multi
    def compute_breaks(self):
        for att_day in self:
            att_day.break_ids.unlink()
            if len(att_day.attendance_ids) <= 1:
                # no break
                continue
            else:
                att_ids = att_day.attendance_ids
                iter_att = iter(att_ids.sorted(key=lambda r: r.check_in))
                previous_att = iter_att.next()
                while True:
                    try:
                        attendance = iter_att.next()
                        start = fields.Datetime.from_string(
                            previous_att.check_out)
                        stop = fields.Datetime.from_string(
                            attendance.check_in)
                        att_break = self.env['hr.attendance.break'].create(
                            {
                                'employee_id': att_day.employee_id.id,
                                'attendance_day_id': att_day.id,
                                'start': start,
                                'stop': stop
                            })
                        att_break.attendance_day_id = att_day
                    except StopIteration:
                        break

    @api.multi
    def recompute_attendance(self):
        for att_day in self:
            att_day.attendance_ids = False
            att_day.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', att_day.employee_id.id),
                ('check_in', '>=', att_day.date + " 00:00:00"),
                ('check_in', '<=', att_day.date + " 23:59:59"),
            ])

    @api.multi
    def recompute_due_hours(self):
        self._compute_due_hours()
