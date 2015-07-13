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


class hr_holidays(models.Model):
    _inherit = "hr.holidays"

    @api.multi
    def _generate(self):
        employee_ids = [holiday.employee_id.id for holiday in self]
        self.env['hr.planning.wizard'].generate(employee_ids)

    @api.multi
    def holidays_validate(self):
        res = super(hr_holidays, self).holidays_validate()
        self._generate()
        return res

    @api.multi
    def holidays_refuse(self):
        res = super(hr_holidays, self).holidays_refuse()
        self._generate()
        return res
