# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class HrAttendanceRules(models.Model):
    _name = 'hr.attendance.rules'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('Name')
    threshold = fields.Float('Threshold', help='Threshold in hours when the '
                                               'duration break change')
    due_break = fields.Integer('Minimum break in minute')
    due_break_total = fields.Integer('Total break due in minute')
