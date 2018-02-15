# -*- coding: utf-8 -*-
# © 2016 Coninckx David (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ResCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    due_hours = fields.Float(string="Due hours")
    break_hours = fields.Float(string="Break duration")