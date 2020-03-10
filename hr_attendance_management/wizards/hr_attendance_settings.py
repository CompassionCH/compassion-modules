# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta, date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAttendanceSettings(models.TransientModel):
    """ Settings configuration for hr.attendance."""

    _inherit = "res.config.settings"

    free_break = fields.Float("Free break (hour)")
    max_extra_hours = fields.Float("Max extra hours")
    beginning_date_for_balance_computation = fields.Date(
        string="Date of beginning of new computation way for balance"
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.multi
    def set_beginning_date(self):
        # self.ensure_one()
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_management.beginning_date_for_balance_computation',
            fields.Date.to_string(date.today().replace(year=2018, month=1, day=1)))

    @api.multi
    def set_free_break(self):
        self.ensure_one()
        if self.free_break < 0:
            raise ValidationError(_("Free break should be positive"))
        if self.free_break != self.get_free_break():
            self.env["ir.config_parameter"].set_param(
                "hr_attendance_management.free_break", str(self.free_break)
            )

    @api.multi
    def set_max_extra_hours(self):
        if self.max_extra_hours < 0:
            raise ValidationError(_("Max extra hours should be positive"))
        # rounding is needed as postgres use less decimal place than python
        if round(self.max_extra_hours, 10) != self.get_max_extra_hours():
            self.env["ir.config_parameter"].set_param(
                "hr_attendance_management.max_extra_hours", str(self.max_extra_hours)
            )

    @api.model
    def get_beginning_date_for_balance_computation(self):
        if (
                not self.env["ir.config_parameter"]
                        .sudo()
                        .get_param(
                    "hr_attendance_management.beginning_date_for_balance_computation",
                    None
                )
        ):
            self.set_beginning_date()

        return fields.Date.to_date(self.env['ir.config_parameter'].get_param(
            'hr_attendance_management.beginning_date_for_balance_computation'))

    @api.model
    def get_free_break(self):
        return float(self.env['ir.config_parameter'].get_param(
            'hr_attendance_management.free_break', '0.0'))

    @api.model
    def get_max_extra_hours(self):
        return float(self.env['ir.config_parameter'].get_param(
            'hr_attendance_management.max_extra_hours', '0.0'))

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            free_break=self.get_free_break(),
            max_extra_hours=self.get_max_extra_hours(),
            beginning_date_for_balance_computation=self.
            get_beginning_date_for_balance_computation(),
        )
        return res

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "free_break", self.set_free_break
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "max_extra_hours", self.set_max_extra_hours
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "beginning_date_for_balance_computation", self.set_beginning_date
        )


class CreateHrAttendance(models.TransientModel):
    _name = "create.hr.attendance.day"

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")
    employee_ids = fields.Many2many("hr.employee", string="Employee", readonly=False)

    def create_attendance_day(self):
        date_to = self.date_to
        att_day = self.env["hr.attendance.day"]

        for employee_id in self.employee_ids:
            current_date = self.date_from
            while current_date <= date_to:
                already_exist = att_day.search(
                    [("employee_id", "=", employee_id.id), ("date", "=", current_date)]
                )
                if not already_exist:
                    att_day.create(
                        {"employee_id": employee_id.id, "date": current_date, }
                    )
                current_date = current_date + timedelta(days=1)
