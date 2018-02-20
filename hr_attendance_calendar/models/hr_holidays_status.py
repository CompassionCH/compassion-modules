# -*- coding: utf-8 -*-
# (C) 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    remove_from_due_hours = fields.Boolean(string="Remove from due hours",
                                           default=False)
