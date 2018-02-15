# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    remove_from_due_hours = fields.Boolean(string="Remove from due hours")
    bonus_hours = fields.Boolean(string="Bonus hours")
    
    def name_get(self, cr, uid, ids, context=None):
        res = super(HrHolidaysStatus, self).name_get(cr, uid, ids, context=context)
        if not context.get('employee_id'):
            return res
        employee = self.pool.get('hr.employee').browse(cr, uid, context.get('employee_id'), context=context)[0]
        res2 = []
        for record in self.browse(cr, uid, ids, context=context):
            if record.bonus_hours:
                for name in res:
                    if name[0] == record.id:
                        name = (record.id, record.name + ('  (%0.2f h)' % (employee.bonus_malus)))
                    res2.append(name)
        return res2

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _check_date(self, cr, uid, ids, context=None):
        return True

    _constraints = [
        (_check_date, '', ['date_from', 'date_to'])
    ]