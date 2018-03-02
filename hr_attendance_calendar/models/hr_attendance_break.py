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


class HrAttendanceBreak(models.Model):
    _name = "hr.attendance.break"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    employee_id = fields.Many2one('hr.employee', "Employee")
    attendance_day_id = fields.Many2one('hr.attendance.day', "Attendance day",
                                        readonly=True,
                                        ondelete="cascade")
    duration = fields.Float('Duration', compute='_compute_duration',
                            store=True, readonly=True)
    start = fields.Datetime("Start", compute='_compute_start_stop', store=True)
    stop = fields.Datetime("Stop", compute='_compute_start_stop', store=True)

    previous_attendance = fields.Many2one('hr.attendance')
    next_attendance = fields.Many2one('hr.attendance')

    system_modified = fields.Boolean('Modified by the system', default=False)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('previous_attendance',)
    def _compute_start_stop(self):
        for rd in self:
            rd.start = rd.previous_attendance.check_out
            rd.stop = rd.next_attendance.check_in

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

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################

    @api.multi
    def write(self, vals):
        for this in self:
            if 'start' in vals:
                this.previous_attendance.write({
                    'check_in': vals['start'],
                    'no_compute_break': True,
                })
            if 'stop' in vals:
                this.next_attendance.write({
                    'check_in': vals['stop'],
                    'no_compute_break': True,
                })
            if 'system_modified' not in vals:
                vals['system_modified'] = False

            super(HrAttendanceBreak, self).write(vals)
