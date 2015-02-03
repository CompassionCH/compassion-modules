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

from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import SUPERUSER_ID
import pytz
from datetime import datetime, timedelta


class hr_planning_wizard(orm.TransientModel):
    _name = 'hr.planning.wizard'

    def generate(self, cr, uid, ids, context=None):
        employee_obj = self.pool.get('hr.employee')
        planning_day_obj = self.pool.get('hr.planning.day')

        # Get employees
        employee_ids = employee_obj.search(cr, uid, [], context=context)
        employees = employee_obj.browse(cr, uid, employee_ids, context=context)

        today = datetime.today()

        # Find the time zone
        tz = self._get_time_zone(cr, uid, context)

        for employee in employees:

            # Clean future planning days
            planning_days_to_remove = planning_day_obj.search(
                cr, uid,
                [('employee_id', '=', employee.id),
                    ('start_date', '>=', today.strftime(DF))],
                context=context)
            planning_day_obj.unlink(
                cr, uid, planning_days_to_remove, context=context)

            for contract in employee.contract_ids:
                for attendance in contract.working_hours.attendance_ids:

                    d = datetime.strptime(contract.date_start, DF)

                    if (d < today):
                        d = today

                    if (not(contract.date_end)):
                        end_date = d+timedelta(days=365)
                    else:
                        end_date = datetime.strptime(contract.date_end, DF)
                        + timedelta(days=1)

                    delta = timedelta(days=1)

                    while d <= end_date:
                        start_hour, start_minutes = self._time_from_float(
                            cr, uid, attendance.hour_from, context)

                        end_hour, end_minutes = self._time_from_float(
                            cr, uid, attendance.hour_to, context)

                        start_date = datetime(
                            d.year, d.month, d.day, start_hour, start_minutes)

                        stop_date = datetime(
                            d.year, d.month, d.day, end_hour, end_minutes)

                        start_date = start_date - tz.utcoffset(start_date)
                        stop_date = stop_date - tz.utcoffset(stop_date)

                        if (int(attendance.dayofweek) == d.weekday()):
                            # Check for holidays
                            holiday_obj = self.pool.get('hr.holidays')
                            holidays = holiday_obj.search(cr, uid, [
                                ('employee_id', '=', employee.id),
                                ('date_from', '<=', start_date.strftime(DF)),
                                ('date_to', '>=', stop_date.strftime(DF)),
                                ('state', '=', 'validate')],
                                context=context)

                            if(len(holidays) == 0):
                                # Create a planning day
                                planning_day_obj.create(cr, uid, {
                                    'employee_id': employee.id,
                                    'contract_id': contract.id,
                                    'start_date': start_date,
                                    'end_date': stop_date})

                        d += delta

    def _get_time_zone(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, SUPERUSER_ID, uid)
        tz = pytz.timezone(user.partner_id.tz) or pytz.utc
        return tz

    def _time_from_float(self, cr, uid, time, context=None):
        hour = int(time)
        minute = int((time - hour)*60)

        return(hour, minute)
