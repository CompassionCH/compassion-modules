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

import openerp
from openerp import models
from openerp.osv import orm, fields
from openerp.tools.translate import _


class hr_planning_day(models.Model):
    _name = "hr.planning.day"
    '''
        Simple model for a working day for an employee.
    # '''
    # _columns = {
        # 'employee_id': fields.many2one(
            # 'hr.employee', 'Employee', readonly=True),
        # 'start_date': fields.datetime('Start date', readonly=True),
        # 'end_date': fields.datetime('End date', readonly=True),
        # 'contract_id': fields.many2one(
            # 'hr.contract', 'Contract', readonly=True),
        # 'department_id': fields.related(
            # 'employee_id', 'department_id',
            # string=_('Department'), type="many2one",
            # relation='hr.department', store=True, readonly=True),
        # 'category_ids': fields.related(
            # 'employee_id', 'category_ids',
            # string=_('Category'), type='many2many',
            # relation='hr.employee.category', store=False, readonly=True),
    # }
    employee_id = openerp.fields.Many2one(
        'hr.employee', 'Employee', readonly=True)
    start_date = openerp.fields.Datetime('Start date', readonly=True)
    end_date = openerp.fields.Datetime('End date', readonly=True)
    contract_id = openerp.fields.Many2one(
        'hr.contract', 'Contract', readonly=True)
    department_id = openerp.fields.Many2one(
        reltated='employee_id.department_id', string=_('Department'),
        store=True, readonly=True)
    category_ids = openerp.fields.Many2many(
        related='employee_id.category_ids', string=_('Category'),
        store=False, readonly=True)
