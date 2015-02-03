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

from openerp.osv import orm


class hr_holidays(orm.Model):
    _inherit = "hr.holidays"

    def create(self, cr, uid, vals, context=None):
        res = super(hr_holidays, self).create(
            cr, uid, vals, context=context)
        self._generate(cr, uid, [res], context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hr_holidays, self).write(
            cr, uid, ids, vals, context=context)
        self._generate(cr, uid, ids, context)
        return res

    def _generate(self, cr, uid, ids, context=None):
        holidays = self.browse(cr, uid, ids, context=context)

        for holiday in holidays:
            employee_ids = []
            employee_ids.append(holiday.employee_id.id)

            self.pool.get('hr.planning.wizard').generate(
                cr, uid, employee_ids, context=context)
