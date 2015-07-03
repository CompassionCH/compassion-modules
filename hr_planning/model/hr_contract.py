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

from openerp import api, models
from openerp.osv import orm


class hr_contract(models.Model):
    _inherit = "hr.contract"

    @api.model
    def create(self, vals):
        res = super(hr_contract, self).create(vals)
        if('working_hours' in vals):
            res._generate()
        return res

    @api.model
    @api.one
    def write(self, vals):
        res = super(hr_contract, self).write(vals)
        if('working_hours' in vals or
           'date_start' in vals or
           'date_end' in vals):
            self._generate()
        return res

    def unlink(self):
        planning_day_ids = self.pool.get('hr.planning.day').search(
            [('contract_id', 'in', self.id)])
        planning_day_ids.unlink()
        res = super(hr_contract, self).unlink(
            cr, uid, ids, context=context)
        return res
    
    @api.model
    def _generate(self):
        employee_ids = []
        for contract in self:
            employee_ids.append(contract.employee_id.id)
        self.pool.get('hr.planning.wizard').generate(
            self.env.cr, self.env.user.id, employee_ids, context=self.env.context)
