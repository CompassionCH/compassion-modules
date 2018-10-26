# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
import pytz

_logger = logging.getLogger(__name__)


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.constrains('state', 'number_of_days_temp', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            # Check that it isn't possible to take less than half a day.
            if holiday.number_of_days_temp % 0.5 != 0:
                raise ValidationError(_(
                    "The number of day can't be less than half a day.\n"
                    "Please verify your leave duration."))
        super(HrHolidays, self)._check_holidays()

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################
    @api.multi
    def action_validate(self):
        res = super(HrHolidays, self).action_validate()
        att_days = self.find_attendance_days()
        att_days.recompute_due_hours()
        return res

    @api.multi
    def action_refuse(self):
        res = super(HrHolidays, self).action_refuse()
        att_days = self.find_attendance_days()
        att_days.recompute_due_hours()
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def find_attendance_days(self):
        att_days = self.env['hr.attendance.day']
        for rd in self:
            att_day = att_days.search([
                ('employee_id', '=', rd.employee_id.id),
                ('date', '>=', rd.date_from),
                ('date', '<=', rd.date_to)
            ])
            # Add leave in attendance day
            att_day.write({'leave_ids': [(4, rd.id)]})
            att_days |= att_day
        return att_days

    @api.multi
    def compute_leave_time(self, str_date):
        """
        Compute leave duration for the day.
        :param str_date: date to compute (string)
        :return: daily leave duration (in hours)
        :rtype: float [0:24]
        """

        start_time = fields.Datetime.from_string(self.date_from)
        end_time = fields.Datetime.from_string(self.date_to)

        # Convert UTC in local timezone
        user_tz = self.employee_id.user_id.tz
        if user_tz:
            local = pytz.timezone(user_tz)
            utc = pytz.timezone('UTC')

            start_time = utc.localize(start_time).astimezone(local)
            end_time = utc.localize(end_time).astimezone(local)

        start_day = fields.Date.from_string(self.date_from)
        end_day = fields.Date.from_string(self.date_to)

        date = fields.Date.from_string(str_date)

        full_day = self.env['base.config.settings'].get_hours_week()/5

        if date == start_day == end_day:
            duration = self.number_of_days_temp * full_day
        elif start_day < date < end_day:
            duration = full_day

        elif date == start_day:
            if start_time.hour <= 12:
                duration = full_day
            else:
                duration = full_day / 2
        elif date == end_day:
            if end_time.hour > 12:
                duration = full_day
            else:
                duration = full_day / 2
        else:
            _logger.error(
                "This attendance day doesn't correspond to this leave"
            )
            duration = 0

        return duration
