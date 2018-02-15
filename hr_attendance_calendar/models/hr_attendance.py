# -*- coding: utf-8 -*-
# (C) 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    calendar_att_ids = fields.Many2many('resource.calendar.attendance',
                                        compute='_compute_calendar_att_ids',
                                        string="Working schedule Lines",
                                        readonly=True)
    calendar_worked_hours = fields.Float(compute='_compute_calendar_att_ids',
                                         string="Worked hours (based on "
                                                "calendar)")

    @staticmethod
    def _match_period(time1_from, time1_to, time2_from, time2_to):
        match_time_from = time1_from
        match_time_to = time1_to
        if time1_to <= time2_from:
            return False, False
        if time1_from >= time2_to:
            return False, False
        if time1_from < time2_from:
            match_time_from = time2_from
        if time1_to > time2_to:
            match_time_to = time2_to
        return match_time_from, match_time_to

    @staticmethod
    def replace_hour_dt(flt_hour, dt):
        hour = int(flt_hour)
        minute = int((flt_hour - int(flt_hour)) * 60)
        second = int((((flt_hour - int(flt_hour)) * 60) - minute) * 60)
        if hour == 24:
            return dt.replace(hour=23, minute=59, second=59)
        return dt.replace(hour=hour, minute=minute, second=second)

    @api.multi
    def _compute_calendar_att_ids(self):
        for attendance in self:
            cal_att_ids = []
            if attendance.check_in and attendance.check_out:
                calendar_worked_hours = 0
                if attendance.employee_id.contract_id.working_hours:
                    working_hours = \
                        attendance.employee_id.contract_id.working_hours

                    for working_hour in working_hours.attendance_ids:
                        attendance_check_in = fields.Datetime.from_string(
                            attendance.check_in)
                        attendance_check_in_ts = \
                            fields.Datetime.context_timestamp(
                                self, attendance_check_in)
                        attendance_check_out = fields.Datetime.from_string(
                            attendance.check_out)
                        attendance_check_out_ts = \
                            fields.Datetime.context_timestamp(
                                self, attendance_check_out)
                        if attendance_check_in and attendance_check_out:
                            if attendance_check_in.weekday() == \
                                attendance_check_out.weekday() and str(
                                attendance_check_in.weekday()) == \
                                working_hour.dayofweek:
                                working_hour_date_from = self.replace_hour_dt(
                                    working_hour.hour_from,
                                    attendance_check_in)
                                working_hour_date_from = \
                                    attendance_check_in_ts.tzinfo.localize(
                                        working_hour_date_from)
                                working_hour_date_to = self.replace_hour_dt(
                                    working_hour.hour_to, attendance_check_out)
                                working_hour_date_to = \
                                    attendance_check_in_ts.tzinfo.localize(
                                        working_hour_date_to)
                                match = self._match_period(
                                    working_hour_date_from,
                                    working_hour_date_to,
                                    attendance_check_in_ts,
                                    attendance_check_out_ts)
                                if match != (False, False):
                                    calendar_worked_hours += (match[1] - match[
                                        0]).total_seconds() / 3600

                                    cal_att_ids.append(working_hour.id)
                    attendance.calendar_worked_hours = calendar_worked_hours
                    attendance.calendar_att_ids = cal_att_ids
