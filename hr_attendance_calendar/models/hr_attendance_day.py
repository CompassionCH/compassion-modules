# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
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
    _sql_constraints = [('unique_product', 'unique(date, employee_id)',
                         'This "Attendance day" already exist for this '
                         'employee')]

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
    name = fields.Char(compute='_compute_name', store=True)

    # Leaves
    leave_ids = fields.Many2many('hr.holidays', readonly=True, string='Leaves')
    in_leave = fields.Boolean('In leave', compute='_compute_in_leave',
                              store=True)
    public_holiday_id = fields.Many2one('hr.holidays.public.line',
                                        'Public holidays')

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
    coefficient = fields.Float(readonly=True, string='Coefficient',
                               help='Worked hours coefficient')

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
    @api.depends('date')
    def _compute_working_day(self):
        for att_day in self.filtered('date'):
            att_day.working_day = fields.Date.from_string(
                att_day.date).strftime('%A')

    @api.multi
    @api.depends('working_day')
    def _compute_name(self):
        for rd in self.filtered('working_day'):
            rd.name = rd.working_day + ' ' + rd.date

    @api.multi
    @api.depends('leave_ids')
    def _compute_in_leave(self):
        for att_day in self:
            if att_day.leave_ids:
                att_day.in_leave = True
            if att_day.public_holiday_id:
                att_day.in_leave = True

    @api.multi
    @api.depends('cal_att_ids', 'cal_att_ids.due_hours', 'leave_ids.state',
                 'public_holiday_id')
    def _compute_due_hours(self):
        """First search the due hours based on the contract and after remove
        somme hours if they are vacation"""
        for att_day in self:
            due_hours = 0
            # Contract
            for cal_att in att_day.cal_att_ids:
                due_hours += cal_att.due_hours
            # Leaves
            if att_day.leave_ids:
                for leave in att_day.leave_ids:
                    if leave.state not in ['validate', 'validate1']:
                        continue
                    if not leave.holiday_status_id.remove_from_due_hours:
                        working_day = self.env[
                            'base.config.settings'].get_work_day_duration()
                        due_hours -= leave.compute_work_day(
                            att_day.date) * working_day
            # Public holidays
            if att_day.public_holiday_id:
                due_hours = 0

            if due_hours < 0:
                due_hours = 0

            att_day.due_hours = due_hours

    @api.multi
    @api.depends('attendance_ids.worked_hours')
    def _compute_worked_hours(self):
        for att_day in self.filtered('attendance_ids'):
            worked_hours = sum(att_day.attendance_ids.mapped('worked_hours'))

            # Take only the breaks edited by the system
            breaks = att_day.break_ids.filtered(lambda r: r.system_modified)

            for break_id in breaks:
                if break_id.is_offered:
                    continue
                if break_id.logged_duration:
                    # the break was modified
                    deduct = break_id.logged_duration - \
                             break_id.original_duration
                else:
                    # the break was created
                    deduct = break_id.logged_duration
                worked_hours -= deduct

            att_day.worked_hours = worked_hours

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
    @api.depends('break_ids', 'break_ids.logged_duration')
    def _compute_break_max(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_max = max(
                att_day.break_ids.mapped('logged_duration'))

    @api.multi
    @api.depends('break_ids', 'break_ids.logged_duration')
    def _compute_break_total(self):
        for att_day in self.filtered('break_ids'):
            att_day.break_total = sum(
                att_day.break_ids.mapped('logged_duration'))

    @api.multi
    @api.depends('worked_hours', 'due_hours', 'coefficient')
    def _compute_extra_hours(self):
        for att_day in self.filtered('coefficient'):
            extra_hours = att_day.worked_hours - att_day.due_hours
            coefficient = att_day.coefficient

            att_day.extra_hours = extra_hours * coefficient

    @api.multi
    def breaks_is_valid(self):
        for att_day in self:
            rule = att_day.rule_id

            worked_hours = att_day.worked_hours

            # Find the rule corresponding to worked_hours
            if not (rule.time_from <= worked_hours < rule.time_to):
                rule = self.env['hr.attendance.rules'].search([
                    ('time_to', '>', worked_hours),
                    '|', ('time_from', '<=', worked_hours),
                    ('time_from', '=', False),
                ])

            breaks_total = sum(att_day.break_ids.mapped('logged_duration'))
            break_max = max(att_day.break_ids.mapped('logged_duration'))

            respect_min = break_max >= rule.due_break
            respect_total = breaks_total >= rule.due_break_total

            if respect_total and respect_min:
                # breaks valid
                return
            elif not respect_min:
                due_break = rule.due_break
            else:
                due_break = rule.due_break_total
                for break_id in att_day.break_ids:
                    if break_id.is_offered:
                        due_break -= break_id.logged_duration

            # Extend the break duration
            att_breaks = att_day.break_ids.filtered(
                lambda r: not r.is_offered)

            if att_breaks:
                att_break = att_breaks.sorted('logged_duration')[-1]
            # if not exist create a new one
            else:
                att_break = self.env['hr.attendance.break'].create({
                    'employee_id': att_day.employee_id.id,
                    'attendance_day_id': att_day.id
                })

            att_break.write({
                'system_modified': True,
                'modified_duration': due_break,
            })

            return att_day.breaks_is_valid()

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
            if cal_att_id.date_from:
                start = fields.Date.from_string(cal_att_id.date_from)
            else:
                start = date.min
            if cal_att_id.date_to:
                end = fields.Date.from_string(cal_att_id.date_to)
            else:
                end = date.max
            if start <= cal_att_date <= end:
                rd.cal_att_ids += cal_att_id

        # link to leaves (hr.holidays )
        date_str = fields.Date.to_string(cal_att_date)
        rd.leave_ids = self.env['hr.holidays'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '<=', date_str),
            ('date_to', '>=', date_str)])

        # find coefficient TODO: review
        co_ids = self.env['hr.weekday.coefficient'].search([
            ('day_of_week', '=', week_day)]).filtered(
            lambda r: r.category_ids & rd.employee_id.category_ids)
        if co_ids:
            rd.coefficient = co_ids.coefficient if len(
                co_ids) == 1 else co_ids[0].coefficient
        else:
            rd.coefficient = 1

        # check public holiday
        if self.env['hr.holidays.public'].is_public_holiday(
            rd.date, rd.employee_id.id):
            holidays_lines = self.env[
                'hr.holidays.public'].get_holidays_list(
                cal_att_date.year, rd.employee_id.id)
            rd.public_holiday_id = holidays_lines.filtered(
                lambda r: r.date == rd.date)

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

            # add the offered break
            free_break = self.env['base.config.settings'].get_free_break()
            if free_break > 0:
                rd = self.env['hr.attendance.break'].create(
                    {
                        'employee_id': att_day.employee_id.id,
                        'attendance_day_id': att_day.id,
                        'is_offered': True,
                        'system_modified': True,
                    })
                rd.write({'modified_duration': free_break})

            att_ids = att_day.attendance_ids
            iter_att = iter(att_ids.sorted(key=lambda r: r.check_in))
            previous_att = iter_att.next()
            while True:
                try:
                    attendance = iter_att.next()
                    self.env['hr.attendance.break'].create(
                        {
                            'employee_id': att_day.employee_id.id,
                            'attendance_day_id': att_day.id,
                            'previous_attendance': previous_att.id,
                            'next_attendance': attendance.id,
                        })
                    previous_att = attendance
                except StopIteration:
                    break

            # valid break
            att_day.breaks_is_valid()
        self._compute_worked_hours()

    @api.multi
    def recompute_attendance(self):
        for att_day in self:
            att_day.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', att_day.employee_id.id),
                ('check_in', '>=', att_day.date + " 00:00:00"),
                ('check_in', '<=', att_day.date + " 23:59:59"),
            ])
        self._compute_extra_hours()

    @api.multi
    def recompute_due_hours(self):
        self._compute_due_hours()
