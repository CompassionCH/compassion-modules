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

    def _generate(self, cr, uid, ids, context=None):
        holidays = self.browse(cr, uid, ids, context=context)
        employee_ids = [holiday.employee_id.id for holiday in holidays]
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, employee_ids, context=context)

    def holidays_validate(self, cr, uid, ids, context=None):
        res = super(hr_holidays, self).holidays_validate(
            cr, uid, ids, context=context)
        self._generate(cr, uid, ids, context)
        return res

    def holidays_refuse(self, cr, uid, ids, context=None):
        res = super(hr_holidays, self).holidays_refuse(
            cr, uid, ids, context=context)
        self._generate(cr, uid, ids, context)
        return res
