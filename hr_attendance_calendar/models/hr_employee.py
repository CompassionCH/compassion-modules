# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Open Net Sarl (https://www.open-net.ch)
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    extra_hours = fields.Float('Extra hours',
                               compute='_compute_extra_hours',
                               readonly=True,
                               oldname='bonus_malus')
    extra_hours_lost = fields.Float("Extra hours lost",
                                    readonly=True, store=True)
    attendance_days_ids = fields.One2many('hr.attendance.day', 'employee_id',
                                          "Attendance day")
    annual_balance = fields.Float('Annual balance')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    @api.depends('attendance_days_ids.extra_hours')
    def _compute_extra_hours(self):
        for employee in self:

            current_year = date.today().replace(month=1, day=1)

            attendance_day_ids = employee.attendance_days_ids.filtered(
                lambda r: r.date >= current_year.strftime('%x'))

            extra_hours_sum = sum(attendance_day_ids.mapped('extra_hours'))

            employee.extra_hours = extra_hours_sum + employee.annual_balance

    @api.model
    def _cron_create_attendance(self):
        employees = self.search([])
        today = fields.Date.today()
        for employee in employees:
            if today in employee.attendance_days_ids.mapped['date']:
                continue
            contract_date_start = fields.Date.from_string(
                employee.contract_id.date_start)
            contract_date_end = fields.Date.from_string(
                employee.contract_id.date_end)
            if contract_date_start < today < contract_date_end:
                if employee.contract_id.working_hours:
                    self.env['hr.attendance.day'].create({
                        'date': today,
                        'employee_id': employee.id
                    })
