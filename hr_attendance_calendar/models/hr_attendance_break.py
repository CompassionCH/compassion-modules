# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class HrAttendanceBreak(models.Model):
    _name = "hr.attendance.break"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string="Employee")
    attendance_day_id = fields.Many2one(comodel_name='hr.attendance.day',
                                        string="Attendance day",
                                        readonly=True,
                                        ondelete="cascade")
    duration = fields.Float(string='Duration',
                            compute='_compute_duration',
                            store=True,
                            readonly=True)
    start = fields.Datetime(string="Start")
    stop = fields.Datetime(string="Stop")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('start', 'stop')
    def _compute_duration(self):
        for att_break in self:
            if not att_break.stop:
                att_break.duration = 0
            else:
                start = fields.Datetime.from_string(att_break.start)
                stop = fields.Datetime.from_string(att_break.stop)
                delta = stop - start
                att_break.duration = delta.total_seconds() / 3600.0
