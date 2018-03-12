# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import tools
from odoo import models, fields, api


class ExtraHoursEvolutionDayReport(models.Model):
    _name = "hr_attendance_day.extra_hours_evolution_day_report"
    _table = "extra_hours_evolution_day_report"
    _description = "Extra hours evolution by days"
    _auto = False
    _rec_name = 'hr_date'

    hr_date = fields.Char(string="Date", readonly=True)
    employee_id = fields.Integer(string="employee_id")
    balance = fields.Float(string="Balance")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(
            self.env.cr, self._table)

        self.env.cr.execute("""
        CREATE OR REPLACE VIEW extra_hours_evolution_day_report AS
        SELECT sub.hr_date AS hr_date,
               ROW_NUMBER() OVER (
                                  ORDER BY
                                    (SELECT 100)) AS id,
               sum(sub.extra_hours) OVER (PARTITION BY sub.employee_id
                                          ORDER BY sub.hr_date) AS balance,
               sub.employee_id AS employee_id
        FROM
          (SELECT to_char(date_trunc('day', hr.date), 'YYYY-MM-DD') AS hr_date,
                   sum(hr.extra_hours) AS extra_hours,
                   hr.employee_id AS employee_id
           FROM hr_attendance_day AS hr
           WHERE hr.date < now()
           GROUP BY date_trunc('day', hr.date),
                    hr.employee_id
           ORDER BY hr_date) AS sub
        ORDER BY hr_date
        """)
