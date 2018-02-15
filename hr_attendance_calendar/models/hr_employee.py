# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta, datetime

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.depends('attendance_days_ids')
    def _compute_bonus_malus(self):
        att_day = self.env['hr.attendance.day']
        for employee in self:
            att_days = att_day.search([
                ('employee_id', '=', employee.id)
            ])
            employee.bonus_malus = sum([att_day.total_bonus_malus for att_day in att_days])

    bonus_malus = fields.Float(string="Bonus/Malus", compute=_compute_bonus_malus, store=True)
    attendance_days_ids = fields.One2many('hr.attendance.day', 'employee_id', string="Calcul des présences par jour")

    @api.model
    def _cron_create_attendance_computation(self):
        employees = self.search([])
        att_day = self.env['hr.attendance.day']
        last_day = datetime.today() - timedelta(days=1)
        for employee in employees:
            if employee.contract_id:
                if employee.contract_id.working_hours:
                    att_days = att_day.search([('name', '=', last_day),('employee_id', '=', employee.id)])
                    if not att_days:
                        att_day.create({
                            'name':last_day,
                            'employee_id':employee.id
                        })


