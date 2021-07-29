# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = "hr.leave"

    attendance_day_ids = fields.Many2many(
        "hr.attendance.day",
        store=True,
        string="Attendances days",
        compute="_compute_att_day",
        readonly=False,
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.depends("date_from", "date_to", "state")
    @api.multi
    def _compute_att_day(self):
        att_days = self.env["hr.attendance.day"]
        for rd in self:
            # Remove the current leave from the attendance_day.leave_ids in
            # case of the date change
            for att in rd.attendance_day_ids:
                if self in att.leave_ids:
                    att.leave_ids = att.leave_ids.filtered(lambda r: r.id != rd.id)

            att_days = att_days.search(
                [
                    ("employee_id", "=", rd.employee_id.id),
                    ("date", ">=", rd.date_from),
                    ("date", "<=", rd.date_to),
                ]
            )

            rd.sudo().attendance_day_ids = att_days

            for att_day in att_days:
                att_day.leave_ids = att_day.leave_ids | self

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            res = employee.get_work_days_data(date_from, date_to)
            # we extract the hour instead of the day. dividing the total leave hours by 8
            # allows us to take into account employees that work part time (instead of subtracting whole days)
            return res['hours'] / 8.0

        return super()._get_number_of_days(date_from, date_to, employee_id)
