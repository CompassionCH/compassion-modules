# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp import SUPERUSER_ID
import pytz
from datetime import datetime, timedelta, time


class hr_planning_wizard(models.TransientModel):
    _name = 'hr.planning.wizard'

    # Global regeneration from wizard
    @api.multi
    def regenerate(self):
        employees = self.env['hr.employee'].search([])
        self.generate(employees.ids)

    @api.multi
    def generate(self, employee_ids):
        planning_day_obj = self.env['hr.planning.day']
        employees = self.env['hr.employee'].browse(employee_ids)
        today = datetime.today()
        # Find the time zone
        tz = self._get_time_zone()
        for employee in employees:

            # Clean future planning days
            planning_days_to_remove = planning_day_obj.search(
                [('employee_id', '=', employee.id),
                 ('start_date', '>=', today.strftime(DF))])
            planning_days_to_remove.unlink()

            # Loop on each contract related to the employee
            for contract in employee.contract_ids:
                if not contract.working_hours.attendance_ids:
                    continue
                # Loop on each day of the schedule
                for attendance in contract.working_hours.attendance_ids:

                    d = datetime.strptime(contract.date_start, DF)

                    if (d < today):
                        d = today
                    # CDI
                    if (not(contract.date_end)):
                        end_date = d + timedelta(days=365)
                    # CDD
                    else:
                        end_date = datetime.strptime(
                            contract.date_end, DF) + timedelta(days=1)

                    delta = timedelta(days=1)

                    # Loop until the end_date is reached
                    while d <= end_date:
                        start_hour, start_minutes = self._time_from_float(
                            attendance.hour_from)

                        end_hour, end_minutes = self._time_from_float(
                            attendance.hour_to)

                        start_date = datetime(
                            d.year, d.month, d.day, start_hour, start_minutes)

                        stop_date = datetime(
                            d.year, d.month, d.day, end_hour, end_minutes)

                        # Fix time zone issue
                        start_date = start_date - tz.utcoffset(start_date)
                        stop_date = stop_date - tz.utcoffset(stop_date)

                        if (int(attendance.dayofweek) == d.weekday()):
                            # Check for holidays
                            holiday_obj = self.env['hr.holidays']
                            holidays = holiday_obj.search([
                                ('employee_id', '=', employee.id),
                                ('date_from', '<=', start_date.strftime(DF)),
                                ('date_to', '>=', stop_date.strftime(DF)),
                                ('state', '=', 'validate')])
                            # If no holidays on the full day
                            if not holidays:
                                # Create a planning day
                                planning_day_obj.create({
                                    'employee_id': employee.id,
                                    'contract_id': contract.id,
                                    'start_date': start_date,
                                    'end_date': stop_date})
                            # If holidays on a part of the day
                            elif len(holidays) == 1:
                                holiday = holidays[0]
                                holiday_start = datetime.strptime(
                                    holiday.date_from, DTF)
                                holiday_stop = datetime.strptime(
                                    holiday.date_to, DTF)

                                if (holiday_start.date() == d.date() and
                                        start_date < holiday_start):
                                    planning_day_obj.create({
                                        'employee_id': employee.id,
                                        'contract_id': contract.id,
                                        'start_date': start_date,
                                        'end_date': holiday_start})
                                elif (holiday_stop.date() == d.date() and
                                        stop_date > holiday_stop):
                                    planning_day_obj.create({
                                        'employee_id': employee.id,
                                        'contract_id': contract.id,
                                        'start_date': holiday_stop,
                                        'end_date': stop_date})
                        d += delta
            # Planning days exceptions
            self._move_planning_days(employee)

    @api.model
    def _move_planning_days(self, employee):

        # Search for validated request
        planning_day_move_requests = self.env[
            'hr.planning.day.move.request'].search(
            [('employee_id', '=', employee.id), ('state', '=', 'validate')])

        planning_day_obj = self.env['hr.planning.day']
        planning_days = planning_day_obj.search(
            [('employee_id', '=', employee.id)])

        for planning_day_move_request in planning_day_move_requests:
            # Move case
            if (planning_day_move_request.type == 'move'):
                # Find the day to move
                for planning_day in planning_days:
                    if (datetime.strptime(
                            planning_day_move_request.old_date, DF).date() ==
                            datetime.strptime(
                                planning_day.start_date, DTF).date()):
                        new_start_date = datetime.combine(
                            datetime.strptime(
                                planning_day_move_request.new_date, DF).date(),
                            datetime.strptime(
                                planning_day.start_date, DTF).time()
                        )
                        new_end_date = datetime.combine(
                            datetime.strptime(
                                planning_day_move_request.new_date, DF).date(),
                            datetime.strptime(
                                planning_day.end_date, DTF).time()
                        )
                        # Update the day
                        planning_day.write({
                            'start_date': new_start_date,
                            'end_date': new_end_date})
            # Add case
            else:
                start_hour, start_minutes = self._time_from_float(
                    planning_day_move_request.hour_from)
                end_hour, end_minutes = self._time_from_float(
                    planning_day_move_request.hour_to)
                new_start_date = datetime.combine(
                    datetime.strptime(
                        planning_day_move_request.new_date, DF).date(),
                    time(start_hour, start_minutes)
                )
                new_end_date = datetime.combine(
                    datetime.strptime(
                        planning_day_move_request.new_date, DF).date(),
                    time(end_hour, end_minutes)
                )
                tz = self._get_time_zone()
                new_start_date = new_start_date - tz.utcoffset(new_start_date)
                new_end_date = new_end_date - tz.utcoffset(new_end_date)

                # Create a new planning day
                planning_day_obj.create(
                    {'start_date': new_start_date,
                     'end_date': new_end_date,
                     'employee_id': employee.id})

    @api.model
    def _get_time_zone(self):
        usr = self.env['res.users'].browse(SUPERUSER_ID)
        tz = pytz.utc if not usr.partner_id.tz else pytz.timezone(
            usr.partner_id.tz)
        return tz

    @api.model
    def _time_from_float(self, flt_time):
        hour = int(flt_time)
        minute = int((flt_time - hour) * 60)
        return(hour, minute)
