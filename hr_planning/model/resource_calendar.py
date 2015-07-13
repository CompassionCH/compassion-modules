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


class resource_calendar(models.Model):
    _inherit = 'resource.calendar'

    @api.model
    def create(self, vals):
        res = super(resource_calendar, self).create(vals)

        if ('attendance_ids' in vals):
            res._generate()
        return res

    def write(self, vals):
        res = super(resource_calendar, self).write(vals)

        if ('attendance_ids' in vals):
            self._generate()
        return res

    @api.model
    def _generate(self):
        for calendar in self:
            contract_obj = self.env['hr.contract']
            contracts = contract_obj.search(
                [('working_hours', '=', calendar.id)])

            employee_ids = []

            for contract in contracts:
                employee_ids.append(contract.employee_id.id)

            self.env['hr.planning.wizard'].generate(employee_ids)
