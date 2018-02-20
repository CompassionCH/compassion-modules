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


class GiftThresholdSettings(models.TransientModel):
    """ Settings configuration for hr.attendance."""
    _name = "hr.attendance.settings"
    _inherit = 'res.config.settings'

    work_day_duration = fields.Float(string='Work day duration')
    free_break = fields.Float(string='Free break')
    attendance_rules = fields.Many2one(comodel_name='hr.attendance.rules',
                                       string='Attendance break rules')
