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

    name = fields.Char('Description', compute='_compute_name')
    employee_id = fields.Many2one('hr.employee', "Employee")
    attendance_day_id = fields.Many2one('hr.attendance.day', "Attendance day",
                                        readonly=True,
                                        ondelete="cascade")
    original_duration = fields.Float('Duration', store=True, readonly=True,
                                     compute='_compute_original_duration')
    modified_duration = fields.Float(readonly=True)
    logged_duration = fields.Float('Logged duration', readonly=True,
                                   store=True,
                                   compute='_compute_logged_duration')

    is_offered = fields.Boolean('Is offered', default=False)
    system_modified = fields.Boolean('Modified by the system', default=False)

    start = fields.Datetime("Start", compute='_compute_start_stop', store=True)
    stop = fields.Datetime("Stop", compute='_compute_start_stop', store=True)

    previous_attendance = fields.Many2one('hr.attendance')
    next_attendance = fields.Many2one('hr.attendance')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('logged_duration')
    def _compute_name(self):
        for rd in self:
            if rd.is_offered:
                rd.name = 'Free break'
            elif not rd.start:
                rd.name = 'Created by the system'
            else:
                start = fields.Datetime.from_string(rd.start)
                start = fields.Datetime.context_timestamp(
                    rd.employee_id, start)
                start = fields.Datetime.to_string(start)[-8:]
                stop = fields.Datetime.from_string(rd.stop)
                stop = fields.Datetime.context_timestamp(
                    rd.employee_id, stop)
                stop = fields.Datetime.to_string(stop)[-8:]
                rd.name = start + ' - ' + stop

    @api.multi
    @api.depends('previous_attendance', )
    def _compute_start_stop(self):
        for rd in self:
            rd.start = rd.previous_attendance.check_out
            rd.stop = rd.next_attendance.check_in

    @api.multi
    @api.depends('start', 'stop')
    def _compute_original_duration(self):
        for att_break in self:
            if not att_break.stop:
                att_break.original_duration = 0
            else:
                start = fields.Datetime.from_string(att_break.start)
                stop = fields.Datetime.from_string(att_break.stop)
                delta = stop - start
                att_break.original_duration = delta.total_seconds() / 3600.0

    @api.multi
    @api.depends('original_duration', 'modified_duration')
    def _compute_logged_duration(self):
        for rd in self:
            rd.logged_duration = rd.modified_duration if \
                rd.modified_duration else rd.original_duration

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################
