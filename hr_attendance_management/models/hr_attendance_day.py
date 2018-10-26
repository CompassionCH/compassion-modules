# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
#    @author: Emanuel Cino <ecino@compassion.ch>
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
    _description = "Attendance day"
    _order = 'date DESC'
    _sql_constraints = [('unique_attendance_day', 'unique(date, employee_id)',
                         'This "Attendance day" already exists for this '
                         'employee')]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    date = fields.Date(required=True, default=fields.Date.today())
    employee_id = fields.Many2one(
        'hr.employee', "Employee", ondelete="cascade", required=True,
        default=lambda self: self.env.user.employee_ids[0].id)

    # Working schedule
    cal_att_ids = fields.Many2many('resource.calendar.attendance',
                                   string="Working schedule",
                                   required=True)
    working_day = fields.Char(compute='_compute_working_day',
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

    has_change_day_request = fields.Boolean(
        compute='_compute_has_linked_change_day_request', store=True,
        oldname='has_linked_change_day_request'
    )

    # Worked
    paid_hours = fields.Float(
        compute='_compute_paid_hours', store=True, readonly=True
    )
    free_breaks_hours = fields.Float(compute='_compute_free_break_hours')
    total_attendance = fields.Float(
        compute='_compute_total_attendance', store=True,
        help='Sum of all attendances of the day'
    )

    coefficient = fields.Float(help='Worked hours coefficient')

    # Break
    due_break_min = fields.Float('Minimum break due',
                                 compute='_compute_due_break')
    due_break_total = fields.Float('Total break due',
                                   compute='_compute_due_break')
    break_ids = fields.One2many('hr.attendance.break',
                                'attendance_day_id',
                                'Breaks',
                                readonly=True)
    break_total = fields.Float('Total break',
                               compute='_compute_break_total',
                               store=True)
    rule_id = fields.Many2one('hr.attendance.rules', 'Rules',
                              compute='_compute_rule_id')

    # Extra hours
    extra_hours = fields.Float("Extra hours",
                               compute='_compute_extra_hours',
                               store=True)
    extra_hours_lost = fields.Float(readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def get_related_forced_due_hours(self):
        self.ensure_one()
        return self.env['hr.forced.due.hours'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '=', self.date)])

    @api.multi
    @api.depends('due_hours')
    def _compute_has_linked_change_day_request(self):
        for att_day in self:
            res = att_day.get_related_forced_due_hours()
            att_day.has_change_day_request = len(res) == 1

    @api.multi
    @api.depends('date')
    def _compute_working_day(self):
        for att_day in self:
            att_day.working_day = fields.Date.from_string(
                att_day.date).strftime('%A').title()

    @api.multi
    @api.depends('working_day')
    def _compute_name(self):
        for rd in self:
            rd.name = rd.working_day + ' ' + rd.date

    @api.multi
    @api.depends('leave_ids', 'public_holiday_id')
    def _compute_in_leave(self):
        for att_day in self:
            att_day.in_leave = att_day.leave_ids or att_day.public_holiday_id

    @api.multi
    @api.depends('cal_att_ids', 'cal_att_ids.due_hours', 'leave_ids.state',
                 'public_holiday_id')
    def _compute_due_hours(self):
        """First search the due hours based on the contract and after remove
        some hours if they are vacation"""
        for att_day in self:

            # Forced due hours (when an user changes work days)
            forced_hours = att_day.get_related_forced_due_hours()
            if forced_hours:
                due_hours = forced_hours.forced_due_hours
            else:
                due_hours = sum(att_day.mapped('cal_att_ids.due_hours'))

            # Public holidays
            if att_day.public_holiday_id:
                att_day.due_hours = 0
                continue

            # Leaves
            for leave in att_day.leave_ids.filtered(
                    lambda l: l.state == 'validate' and not
                    l.holiday_status_id.keep_due_hours):
                due_hours -= leave.compute_leave_time(att_day.date)

            if due_hours < 0:
                due_hours = 0
            att_day.due_hours = due_hours

    @api.multi
    @api.depends('attendance_ids.worked_hours')
    def _compute_total_attendance(self):
        for att_day in self.filtered('attendance_ids'):
            att_day.total_attendance = sum(
                att_day.attendance_ids.mapped('worked_hours') or [0])

    @api.multi
    @api.depends('attendance_ids.worked_hours')
    def _compute_paid_hours(self):
        """
        Paid hours are the sum of the attendances minus the break time
        added by the system if the employee didn't take enough break.
        """
        for att_day in self.filtered('attendance_ids'):
            paid_hours = att_day.total_attendance

            # Take only the breaks edited by the system
            breaks = att_day.break_ids.filtered(
                lambda r: r.system_modified and not r.is_offered)

            paid_hours -= sum(breaks.mapped('additional_duration'))
            att_day.paid_hours = paid_hours

    @api.multi
    def _compute_free_break_hours(self):
        for att_day in self:
            att_day.free_breaks_hours = sum(att_day.break_ids.filtered(
                'is_offered').mapped('total_duration') or [0])

    @api.multi
    @api.depends('attendance_ids')
    def _compute_rule_id(self):
        """
        To know which working rule is applied on the day, we deduce the
        free break time offered from the paid hours.
        """
        for att_day in self:
            if att_day.paid_hours:
                hours = att_day.paid_hours - att_day.free_breaks_hours
            else:
                hours = att_day.due_hours - att_day.free_breaks_hours
            if hours < 0:
                hours = 0
            att_day.rule_id = self.env['hr.attendance.rules'].search([
                ('time_from', '<=', hours),
                ('time_to', '>', hours),
            ])

    @api.multi
    def _compute_due_break(self):
        """Calculation of the break duration due depending of
        hr.attendance.rules (only for displaying it in the view)"""
        for att_day in self:
            if att_day.rule_id:
                att_day.due_break_min = att_day.rule_id.due_break
                att_day.due_break_total = att_day.rule_id.due_break_total
            else:
                att_day.due_break_min = 0
                att_day.due_break_total = 0

    @api.multi
    @api.depends('break_ids', 'break_ids.total_duration')
    def _compute_break_total(self):
        for att_day in self:
            att_day.break_total = sum(
                att_day.break_ids.mapped('total_duration') or [0])

    @api.multi
    @api.depends('paid_hours', 'due_hours', 'coefficient',
                 'extra_hours_lost')
    def _compute_extra_hours(self):
        for att_day in self.filtered('coefficient'):
            extra_hours = att_day.paid_hours - att_day.due_hours
            coefficient = att_day.coefficient
            att_day.extra_hours = (extra_hours * coefficient) - \
                att_day.extra_hours_lost

    @api.multi
    def write(self, vals):
        super(HrAttendanceDay, self).write(vals)
        if 'paid_hours' in vals or 'coefficient' in vals:
            for att_day in self:
                att_days_future = self.search([
                    ('date', '>=', att_day.date),
                    ('employee_id', '=', att_day.employee_id.id)
                ], order='date')
                att_days_future.update_extra_hours_lost()

        return True

    @api.multi
    def update_extra_hours_lost(self):
        """
        This will set the extra hours lost based on the balance evolution
        of the employee, which is a SQL view.
        """
        max_extra_hours = float(self.env['ir.config_parameter'].get_param(
            'hr_attendance_management.max_extra_hours', 0.0))
        # First reset the extra hours lost
        self.write({'extra_hours_lost': 0})

        for att_day in self:
            # For whatever reason, the search method is unable to search
            # on employee field (gives wrong search results)! Therefore
            # we use a direct SQL query.
            self.env.cr.execute("""
                SELECT balance FROM extra_hours_evolution_day_report
                WHERE employee_id = %s AND hr_date = %s
            """, [att_day.employee_id.id, att_day.date])
            balance = self.env.cr.fetchone()
            balance = balance[0] if balance else 0

            if balance > max_extra_hours > 0:
                overhead = balance - max_extra_hours
                att_day.extra_hours_lost = min(overhead, att_day.extra_hours)
            else:
                att_day.extra_hours_lost = 0

    @api.multi
    def validate_extend_breaks(self):
        """
        This will extend the break time based on the break attendance rules
        of the day. The paid hours will be recomputed after that.
        """

        def extend_longest_break(extension_duration):
            # Extend the break duration
            att_breaks = att_day.break_ids.filtered(
                lambda r: not r.is_offered)

            if att_breaks:
                att_break = att_breaks.sorted('total_duration')[-1]
            # if not exist create a new one
            else:
                att_break = self.env['hr.attendance.break'].create({
                    'employee_id': att_day.employee_id.id,
                    'attendance_day_id': att_day.id
                })

            att_break.write({
                'system_modified': True,
                'additional_duration': extension_duration
            })

        def compute_break_time_to_add(rule):
            breaks_total = sum(
                att_day.break_ids.mapped('total_duration') or [0])
            due_break_total = rule["due_break_total"]
            due_break_min_length = rule["due_break"]

            time_to_add = 0
            break_max = max(
                att_day.break_ids.mapped('total_duration') or [0])
            if break_max < due_break_min_length:
                # We want to extend an non-offered break to at least the
                # minimum value.
                break_max_non_offered = max(att_day.break_ids.filtered(
                    lambda b: not b.is_offered).mapped(
                    'total_duration') or [0])
                time_to_add += due_break_min_length - break_max_non_offered
                breaks_total += time_to_add

            if breaks_total < due_break_total:
                time_to_add += due_break_total - breaks_total

            return time_to_add

        for att_day in self:
            logged_hours = att_day.total_attendance - att_day.free_breaks_hours
            rule = self.env['hr.attendance.rules'].search([
                ('time_to', '>', logged_hours),
                '|', ('time_from', '<=', logged_hours),
                ('time_from', '=', False),
            ])
            time_to_add = compute_break_time_to_add(rule)
            if time_to_add != 0:
                # Ensure we don't fall under another working rule when removing
                # hours from that day
                new_logged_hours = logged_hours - time_to_add
                new_rule = self.env['hr.attendance.rules'].search([
                    ('time_to', '>', new_logged_hours),
                    '|', ('time_from', '<=', new_logged_hours),
                    ('time_from', '=', False),
                ])
                if new_rule != rule:
                    time_to_add = compute_break_time_to_add(new_rule)
                    time_to_add = max(time_to_add, logged_hours -
                                      new_rule.time_to)
                if time_to_add != 0:
                    extend_longest_break(time_to_add)

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################
    @api.model
    def create(self, vals):
        rd = super(HrAttendanceDay, self).create(vals)

        att_date = fields.Date.from_string(rd.date)

        # link to schedule (resource.calendar.attendance)
        rd.update_calendar_attendance()
        # link to leaves (hr.holidays )
        date_str = fields.Date.to_string(att_date)
        rd.leave_ids = self.env['hr.holidays'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '<=', date_str),
            ('date_to', '>=', date_str)])

        # find coefficient
        week_day = att_date.weekday()
        co_ids = self.env['hr.weekday.coefficient'].search([
            ('day_of_week', '=', week_day)]).filtered(
            lambda r: r.category_ids & rd.employee_id.category_ids)
        rd.coefficient = co_ids[0].coefficient if co_ids else 1

        # check public holiday
        if self.env['hr.holidays.public'].is_public_holiday(
                rd.date, rd.employee_id.id):
            holidays_lines = self.env['hr.holidays.public'].get_holidays_list(
                att_date.year, rd.employee_id.id)
            rd.public_holiday_id = holidays_lines.filtered(
                lambda r: r.date == rd.date)

        # find related attendance
        rd.attendance_ids = self.env['hr.attendance'].search([
            ('employee_id', '=', rd.employee_id.id),
            ('date', '=', rd.date),
        ])

        # compute breaks
        rd.compute_breaks()

        return rd

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def update_calendar_attendance(self):
        """
        Find matching calendar attendance given the work schedule of the
        employee.
        :return: None
        """
        for att_day in self:
            att_date = fields.Date.from_string(att_day.date)
            week_day = att_date.weekday()

            # look for a valid contract or take schedule of employee
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', att_day.employee_id.id),
                ('date_start', '<=', att_day.date),
                '|', ('date_end', '=', False), ('date_end', '>=', att_day.date)
            ])
            schedules = contracts.mapped('working_hours')
            if not schedules:
                schedules = att_day.employee_id.calendar_id
            cal_att_ids = self.env['resource.calendar.attendance']

            # select the attendance(s) that are valid today.
            current_cal_att = schedules.mapped('attendance_ids').filtered(
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
                if start <= att_date <= end:
                    cal_att_ids += cal_att_id

            att_day.cal_att_ids = cal_att_ids

    @api.multi
    def compute_breaks(self):
        """
        Given the attendance of the employee, check the break time rules
        and compute the break time of the day. This will then trigger the
        computation of the paid hours for the day
        (total attendance - additional break time added)
        :return: None
        """
        for att_day in self.filtered('attendance_ids'):
            att_day.break_ids.unlink()

            # add the offered break
            free_break = self.env['base.config.settings'].get_free_break()
            if free_break > 0:
                self.env['hr.attendance.break'].create({
                    'employee_id': att_day.employee_id.id,
                    'attendance_day_id': att_day.id,
                    'is_offered': True,
                    'system_modified': True,
                    'additional_duration': free_break
                })

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

            # Extend the break time if needed
            att_day.validate_extend_breaks()
        self._compute_paid_hours()

    @api.multi
    def recompute_due_hours(self):
        self._compute_total_attendance()
        self._compute_due_hours()
        self._compute_paid_hours()
