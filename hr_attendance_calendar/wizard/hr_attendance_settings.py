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


class HrAttendanceSettings(models.TransientModel):
    """ Settings configuration for hr.attendance."""
    _name = "hr.attendance.settings"
    _inherit = 'res.config.settings'

    work_day_duration = fields.Float('Work day duration')
    free_break = fields.Float('Free break (in hour)')
    attendance_rules = fields.Many2one('hr.attendance.rules',
                                       'Attendance break rules')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def set_work_day_duration(self):
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_calendar.work_day_duration',
            str(self.work_day_duration))

    @api.multi
    def set_free_break(self):
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_calendar.free_break',
            str(self.free_break))

    @api.multi
    def set_attendance_rules(self):
        self.env['ir.config_parameter'].set_param(
            'hr_attendance_calendar.attendance_rules',
            str(self.work_day_duration))
