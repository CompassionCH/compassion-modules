# -*- coding: utf-8 -*-
# (C) 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta, datetime
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # TODO: rename bonus_malus to extra_hours
    bonus_malus = fields.Float(string="Bonus/Malus",
                               compute='_compute_bonus_malus', store=True)

    attendance_days_ids = fields.One2many('hr.attendance.day', 'employee_id',
                                          string="Calcul des présences par "
                                                 "jour")

    attendance_quota_green = fields.Integer(string="Limit extra hours green")
    attendance_quota_orange = fields.Integer(string="Limit extra hours orange")
    attendance_quota_red = fields.Integer(string="Limit extra hours red")

    @api.depends('attendance_days_ids')
    def _compute_bonus_malus(self):
        att_day = self.env['hr.attendance.day']
        for employee in self:
            att_days = att_day.search([
                ('employee_id', '=', employee.id)
            ])
            employee.bonus_malus = sum(
                [att_day.total_bonus_malus for att_day in att_days])

    @api.model
    def _cron_create_attendance_computation(self):
        employees = self.search([])
        att_day = self.env['hr.attendance.day']
        last_day = datetime.today() - timedelta(days=1)
        for employee in employees:
            if employee.contract_id:
                if employee.contract_id.working_hours:
                    att_days = att_day.search([('name', '=', last_day), (
                        'employee_id', '=', employee.id)])
                    if not att_days:
                        att_day.create({
                            'name': last_day,
                            'employee_id': employee.id
                        })
