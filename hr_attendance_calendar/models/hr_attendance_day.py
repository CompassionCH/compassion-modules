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

from datetime import date, timedelta

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
    date = fields.Date("Date",
                       # readonly=True, todo: uncomment
                       required=True)
    employee_id = fields.Many2one('hr.employee', "Employee",
                                  ondelete="cascade", required=True)

    # Working schedule
    cal_att_ids = fields.Many2many('resource.calendar.attendance',
                                   string="Working schedule",
                                   required=True)
    working_day = fields.Char("Working day", compute='_compute_working_day',
                              readonly=True, store=True)

    # Leaves
    leave_ids = fields.Many2many('hr.holidays', readonly=True, string='Leaves')
    in_leave = fields.Boolean('In leave', compute='_compute_in_leave',
                              store=True)

    # Due hours
    due_hours = fields.Float('Due hours', compute='_compute_due_hours',
                             readonly=True, store=True)

    # Attendances
    attendance_ids = fields.One2many('hr.attendance', 'attendance_day_id',
                                     'Attendances', readonly=True)

    # Worked
    worked_hours = fields.Float('Worked hours',
                                compute='_compute_worked_hours', store=True,
                                readonly=True)
    logged_hours = fields.Float('Logged hours',
                                compute='_compute_logged_hours', store=True,
                                readonly=True)
    coefficient_id = fields.Many2one('hr.weekday.coefficient', readonly=True)

    # Break
    due_break_min = fields.Float('Minimum break due',
                                 compute='_compute_due_break')
    due_break_total = fields.Float('Total break due',
                                   compute='_compute_due_break')
    break_ids = fields.One2many('hr.attendance.break',
                                'attendance_day_id',
                                'Breaks',
                                readonly=True)
    break_max = fields.Float('Longest break',
                             compute='_compute_break_max',
                             store=True, )
    break_total = fields.Float('Total break',
                               compute='_compute_break_total',
                               store=True, )
    rule_id = fields.Many2one('hr.attendance.rules', 'Rules',
                              compute='_compute_rule_id')

    # Extra hours
    extra_hours = fields.Float("Extra hours",
                               compute='_compute_extra_hours',
                               store=True, )

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
                        working_day = self.env[
                            'base.config.settings'].get_work_day_duration()
                        due_hours -= leave.compute_work_day(
                            att_day.date) * working_day

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
        for att_day in self.filtered('coefficient_id'):
            logged_hours = att_day.worked_hours
            coefficient = att_day.coefficient_id.coefficient

            att_day.logged_hours = logged_hours * coefficient

    @api.multi
    @api.depends('worked_hours', 'due_hours')
    def _compute_rule_id(self):
        for att_day in self:
            more_hours = att_day.worked_hours > att_day.due_hours
            hours = att_day.worked_hours if more_hours else att_day.due_hours

            att_day.rule_id = self.env['hr.attendance.rules'].search([
                ('time_from', '<=', hours),
                ('time_to', '>', hours),
            ])

    @api.multi
    @api.depends('rule_id')
    def _compute_due_break(self):
        """Calculation of the break duration due depending of
        hr.attendance.rules"""
        for att_day in self:
            if att_day.rule_id:
                att_day.due_break_min = att_day.rule_id.due_break
                att_day.due_break_total = att_day.rule_id.due_break_total
            else:
                att_day.due_break_min = 0
                att_day.due_break_total = 0

    @api.multi
    @api.depends('break_ids', 'break_ids.duration')
    def _compute_break_max(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_max = max(att_day.break_ids.mapped('duration'))

    @api.multi
    @api.depends('break_ids', 'break_ids.duration')
    def _compute_break_total(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_total = sum(att_day.break_ids.mapped('duration'))

    @api.multi
    @api.depends('worked_hours', 'due_hours')
    def _compute_extra_hours(self):
        for att_day in self.filtered('worked_hours'):
            att_day.extra_hours = att_day.worked_hours - att_day.due_hours

    @api.multi
    def breaks_validation(self):
        for att_day in self.filtered('break_ids'):
            # local variable
            rule = att_day.rule_id
            free_break = self.env['base.config.settings'].get_free_break()
            worked_hours = att_day.worked_hours
            breaks_total = sum(att_day.break_ids.mapped('duration'))
            break_max = max(att_day.break_ids.mapped('duration'))

            # Find the rule corresponding to worked_hours
            if not (rule.time_from <= worked_hours < rule.time_to):
                rule = self.env['hr.attendance.rules'].search([
                    ('time_to', '>', worked_hours),
                    '|', ('time_from', '<=', worked_hours),
                    ('time_from', '=', False),
                ])

            respect_min = break_max >= rule.due_break
            respect_total = breaks_total + free_break >= rule.due_break_total

            if respect_total and respect_min:
                # breaks valid
                return

            # Extend the break duration
            att_break = att_day.break_ids.sorted('duration')[-1]

            start = fields.Datetime.from_string(att_break.start)
            stop = fields.Datetime.to_string(
                start + timedelta(hours=rule.due_break))
            att_break.write({
                'stop': stop,
                'system_modified': True
            })
            return att_day.breaks_validation()

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################
    @api.model
    def create(self, vals):
        rd = super(HrAttendanceDay, self).create(vals)

        cal_att_date = fields.Date.from_string(rd.date)

        # link to schedule (resource.calendar.attendance)
        week_day = cal_att_date.weekday()
        cal_att_ids = rd.employee_id.contract_id.working_hours.attendance_ids
        current_cal_att = cal_att_ids.filtered(
            lambda a: int(a.dayofweek) == week_day)

        for cal_att_id in current_cal_att:
            start = cal_att_id.date_from or date.min
            end = cal_att_id.date_to or date.max
            if start <= cal_att_date <= end:
                rd.cal_att_ids += cal_att_id

        # link to leaves (hr.holidays )
        date_str = fields.Date.to_string(cal_att_date)
        rd.leave_ids = self.env['hr.holidays'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '<=', date_str),
            ('date_to', '>=', date_str)])

        # find coefficient
        co_ids = self.env['hr.weekday.coefficient'].search([
            ('day_of_week', '=', week_day)]).filtered(
            lambda r: r.category_ids & self.employee_id.category_ids)
        if co_ids:
            self.coefficient_id = co_ids if len(co_ids) == 1 else co_ids[0]

        # find related attendance
        rd.recompute_attendance()

        # compute breaks
        rd.compute_breaks()

        return rd

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def compute_breaks(self):
        for att_day in self.filtered('attendance_ids'):
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
                            'stop': attendance.check_in,
                            'previous_attendance': previous_att.id,
                            'next_attendance': attendance.id,
                        })
                    att_break.attendance_day_id = att_day
                    previous_att = attendance
                except StopIteration:
                    break

            # valid break
            att_day.breaks_validation()

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
