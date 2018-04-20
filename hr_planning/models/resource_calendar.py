# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    @api.model
    def create(self, vals):
        res = super(ResourceCalendar, self).create(vals)

        if ('attendance_ids' in vals):
            res._generate()
        return res

    @api.multi
    def write(self, vals):
        res = super(ResourceCalendar, self).write(vals)

        if ('attendance_ids' in vals):
            self._generate()
        return res

    @api.multi
    def _generate(self):
        for record in self:
            contract_obj = record.env['hr.contract']
            contracts = contract_obj.search(
                [('working_hours', '=', record.id)])

            employee_ids = contracts.mapped('employee_id.id')

            record.env['hr.planning.wizard'].generate(employee_ids)
