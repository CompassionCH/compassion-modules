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


class resource_calendar(orm.Model):
    _inherit = 'resource.calendar'

    def create(self, cr, uid, vals, context=None):
        res = super(resource_calendar, self).create(cr, uid, vals,
                                                    context=context)

        if ('attendance_ids' in vals):
            self._generate(cr, uid, [res], context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(resource_calendar, self).write(
            cr, uid, ids, vals, context=context)

        if ('attendance_ids' in vals):
            self._generate(cr, uid, ids, context)
        return res

    def _generate(self, cr, uid, ids, context=None):
        for id in ids:
            contract_obj = self.pool.get('hr.contract')
            contract_ids = contract_obj.search(
                cr, uid, [('working_hours', '=', id)], context=context)

            contracts = contract_obj.browse(
                cr, uid, contract_ids, context=context)
            employee_ids = []

            for contract in contracts:
                employee_ids.append(contract.employee_id.id)

            self.pool.get('hr.planning.wizard').generate(
                cr, uid, employee_ids, context=context)
