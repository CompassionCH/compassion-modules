# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, fields, api


class HrForcedDueHours(models.Model):
    _name = 'hr.forced.due.hours'
    _order = 'date'

    _sql_constraints = [('unique_due_hours', 'unique(date, employee_id)',
                         'This "Forced due hour" already exists')]

    employee_id = fields.Many2one('hr.employee',
                                  string='Employee', required=True)
    date = fields.Date('Date', required=True)
    forced_due_hours = fields.Float('Forced due hours', required=True)

