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


class HrAttendanceWeighting(models.Model):
    _name = "hr.attendance.weighting"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ],
        string='Day of Week',
        required=True,
        index=True,
        default='0')
    weighting = fields.Float
    category_ids = fields.Many2many(comodel_name='hr.employee.category',
                                    string='Employee tag')
