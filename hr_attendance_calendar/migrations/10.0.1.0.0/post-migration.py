# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date, timedelta

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    employees = env['hr.employee'].search([])

    # create daily report for each employee from 01.01.2018
    for employee in employees:
        # https://stackoverflow.com/a/7274316
        begin_date = date(2018, 1, 1)
        today = date.today()
        delta = today - begin_date

        for i in range(delta.days + 1):
            # create daily report for report_date
            report_date = begin_date + timedelta(days=i)

            env['hr.attendance.day'].create({
                'date': report_date,
                'employee_id': employee.id
            })
