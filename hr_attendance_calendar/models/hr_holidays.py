# -*- coding: utf-8 -*-
# (C) 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    remove_from_due_hours = fields.Boolean(string="Remove from due hours")
    bonus_hours = fields.Boolean(string="Bonus hours")

    @api.multi
    def name_get(self):
        res = super(HrHolidaysStatus, self).name_get()
        if not self.env.context.get('employee_id'):
            return res
        employee = \
            self.env['hr.employee'].browse(
                self.env.context.get('employee_id'))[0]
        result = []
        for record in self:
            if record.bonus_hours:
                for name in res:
                    if name[0] == record.id:
                        name = (record.id, record.name + (
                            '  (%0.2f h)' % employee.bonus_malus))
                    result.append(name)
        return result


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _check_date(self, cr, uid, ids, context=None):
        return True

    _constraints = [
        (_check_date, '', ['date_from', 'date_to'])
    ]
