# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime

import pytz

from odoo import models, fields, api


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    hr_att_day_ids = fields.Many2many(comodel_name='hr.attendance.day',
                                      string='Attendance day related')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def write(self, vals):
        super(HrHolidays, self).write(vals)
        for att_call in self:
            if att_call.state == 'validate' and 'hr_att_day_ids' not in vals:
                start = fields.Date.from_string(att_call.date_from)
                end = fields.Date.from_string(att_call.date_to)
                att_call.hr_att_day_ids = self.env['hr.attendance.day'].search(
                    [('employee_id', '=', att_call.employee_id.id),
                     ('date', '>=', start),
                     ('date', '<=', end)])
                att_call.hr_att_day_ids.recompute_due_hours()

    @api.model
    def compute_work_day(self, str_date):
        """
        Compute if the leave duration for the day is full/half work day.

        :param str_date: date to compute (string)
        :return: daily leave duration (in days)
        :rtype: float [1,0.5]
        """
        tz_employee = pytz.timezone(self.employee_id.user_id.tz)
        date = fields.Datetime.from_string(
            str_date + ' 12:00:00').replace(tzinfo=tz_employee)

        start = pytz.utc.localize(fields.Datetime.from_string(self.date_from))
        end = pytz.utc.localize(fields.Datetime.from_string(self.date_to))

        if start.date() == date.date():
            if start < date:
                return 1
            else:
                return 0.5
        elif end.date() == date.date():
            if end > date:
                return 1
            else:
                return 0.5
        elif start.date() < date.date() < end.date():
            return 1
        else:
            raise IndexError("This attendance day doesn't correspond to this "
                             "leave")
