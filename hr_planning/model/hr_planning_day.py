# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, _


class hr_planning_day(models.Model):
    _name = "hr.planning.day"
    '''
        Simple model for a working day for an employee.
    '''
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', readonly=True)
    start_date = fields.Datetime(readonly=True)
    end_date = fields.Datetime(readonly=True)
    contract_id = fields.Many2one(
        'hr.contract', 'Contract', readonly=True)
    department_id = fields.Many2one(
        'hr.department', reltated='employee_id.department_id',
        string='Department', store=True, readonly=True)
    category_ids = fields.Many2many(
        related='employee_id.category_ids', string='Category',
        store=False, readonly=True)
