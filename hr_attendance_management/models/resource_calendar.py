# Copyright (C) 2016 Open Net Sarl
# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from addons.resource.models.resource import Intervals
from odoo import models, fields, api
from datetime import datetime
from pytz import UTC

_logger = logging.getLogger(__name__)


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals(self, start_dt, end_dt, resource=None):
        """ Return the attendance intervals in the given datetime range after excluding the public holidays.
            The returned intervals are expressed in the resource's timezone.
        """
        if not start_dt.tzinfo:
            start_dt = start_dt.replace(tzinfo=UTC)
        if not end_dt.tzinfo:
            end_dt = end_dt.replace(tzinfo=UTC)

        attendance_intervals = super(ResourceCalendar, self)._attendance_intervals(start_dt, end_dt, resource)

        # By searching for days instead of years then days, we ensure the interval can span over multiple years
        public_holiday = self.env['hr.holidays.public.line'].search([
            ("date", ">=", start_dt),
            ("date", "<=", end_dt)
        ])

        # We represent the public holidays as Intervals to easily remove them from the addendance_intervals
        public_holiday_intervals = Intervals((
            datetime.combine(ph.date, datetime.min.time()).replace(tzinfo=UTC),
            datetime.combine(ph.date, datetime.max.time()).replace(tzinfo=UTC),
            ph
        ) for ph in public_holiday)

        return attendance_intervals - public_holiday_intervals


class ResCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    due_hours = fields.Float(compute="_compute_due_hours", readonly=True)

    @api.multi
    @api.depends("hour_from", "hour_to")
    def _compute_due_hours(self):
        for record in self:
            record.due_hours = record.hour_to - record.hour_from
