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


class HrAttendanceDay(models.Model):
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
    date = fields.Date("Date", oldname='name',
                       # readonly=True, todo: uncomment
                       required=True)
    employee_id = fields.Many2one('hr.employee', "Employee",
                                  ondelete="cascade", required=True)

    # Working schedule
    cal_att_ids = fields.Many2many('resource.calendar.attendance',
                                   string="Working schedule",
                                   required=True)
    working_day = fields.Char("Working day", compute='_compute_working_day',
                              readonly=True,
                              store=True)

    # Leaves
    leave_ids = fields.Many2many('hr.holidays',
                                 'Leaves')
    in_leave = fields.Boolean('In leave', compute='_compute_in_leave',
                              store=True)

    # Due hours
    due_hours = fields.Float('Due hours', compute='_compute_due_hours',
                             readonly=True, store=True)

    # Attendances
    attendance_ids = fields.One2many('hr.attendance',
                                     'attendance_day_id',
                                     'Attendances',
                                     readonly=True)

    # Worked
    worked_hours = fields.Float('Worked hours',
                                compute='_compute_worked_hours',
                                store=True, readonly=True,
                                oldname='calendar_worked_hours')
    logged_hours = fields.Float('Logged hours',
                                compute='_compute_logged_hours',
                                store=True, readonly=True)

    # Break
    # due_break_min = fields.Float('Minimum break due',
    #                              compute='_compute_due_break',
    #                              store=True, )
    # due_break_total = fields.Float('Total break due',
    #                                compute='_compute_due_break',
    #                                store=True, )
    break_ids = fields.One2many('hr.attendance.break',
                                'attendance_day_id',
                                'Breaks',
                                readonly=True, store=True)
    break_max = fields.Float('Longest break',
                             compute='_compute_break_max',
                             store=True, )
    break_total = fields.Float('Total break',
                               compute='_compute_break_total',
                               store=True, )

    # Extra hours
    extra_hours = fields.Float("Extra hours",
                               compute='_compute_extra_hours',
                               store=True, oldname='total_bonus_malus')
    weighting = fields.Float("Weighting",
                             readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('cal_att_ids')
    def _compute_working_day(self):
        for att_day in self.filtered('cal_att_ids'):
            att_day.working_day = fields.Date.from_string(
                att_day.date).strftime('%A')

    @api.multi
    @api.depends('leave_ids')
    def _compute_in_leave(self):
        for att_day in self:
            if att_day.leave_ids:
                att_day.in_leave = True

    @api.multi
    @api.depends('cal_att_ids', 'leave_ids.state')
    def _compute_due_hours(self):
        """First search the due hours based on the contract and after remove
        somme hours if they are vacation"""
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
            att_day.worked_hours = sum(
                att_day.attendance_ids.mapped('worked_hours'))

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
    #                               ORM METHODS                              #
    ##########################################################################
    @api.model
    def create(self, vals):
        rd = super(HrAttendanceDay, self).create(vals)

        cal_att_date = fields.Date.from_string(rd.date)

        # link to schedule (resource.calendar.attendance)
        att_day = cal_att_date.weekday()
        cal_att_ids = rd.employee_id.contract_id.working_hours.attendance_ids
        current_cal_att = cal_att_ids.filtered(
            lambda a: int(a.dayofweek) == att_day)

        for cal_att_id in current_cal_att:
            start = cal_att_id.date_from or date.min
            end = cal_att_id.date_to or date.max
            if start <= cal_att_date <= end:
                rd.cal_att_ids += cal_att_id

        # link to leaves (hr.holidays )
        rd.leave_ids = self.env['hr.holidays'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '<=', cal_att_date),
            ('date_to', '>=', cal_att_date)])

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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def compute_breaks(self):
        for att_day in self:
            att_day.break_ids.unlink()
            if len(att_day.attendance_ids) <= 1:
                # no break
                continue
            att_ids = att_day.attendance_ids
            iter_att = iter(att_ids.sorted(key=lambda r: r.check_in))
            previous_att = iter_att.next()
            while True:
                try:
                    attendance = iter_att.next()
                    att_break = self.env['hr.attendance.break'].create(
                        {
                            'employee_id': att_day.employee_id.id,
                            'attendance_day_id': att_day.id,
                            'start': previous_att.check_out,
                            'stop': attendance.check_in
                        })
                    att_break.attendance_day_id = att_day
                except StopIteration:
                    break

    @api.multi
    def recompute_attendance(self):
        for att_day in self:
            att_day.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', att_day.employee_id.id),
                ('check_in', '>=', att_day.date + " 00:00:00"),
                ('check_in', '<=', att_day.date + " 23:59:59"),
            ])

    @api.multi
    def recompute_due_hours(self):
        self._compute_due_hours()
