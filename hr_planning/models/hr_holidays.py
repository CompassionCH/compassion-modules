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


class HrHolidays(models.Model):
    _inherit = "hr.holidays"

    @api.multi
    def _generate(self):
        employee_ids = self.mapped('employee_id.id')
        self.env['hr.planning.wizard'].generate(employee_ids)

    @api.multi
    def holidays_validate(self):
        res = super(HrHolidays, self).holidays_validate()
        self._generate()
        return res

    @api.multi
    def holidays_refuse(self):
        res = super(HrHolidays, self).holidays_refuse()
        self._generate()
        return res
