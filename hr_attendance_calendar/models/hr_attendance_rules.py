# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class HrAttendanceRules(models.Model):
    _name = 'hr.attendance.rules'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(string='Name')
    threshold = fields.Float(string='Hours threshold in the day')
    due_break = fields.Integer(string='Minimum break in minute')
    due_break_total = fields.Integer(string='Total break due in minute')
