# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Open Net Sarl (https://www.open-net.ch)
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Eicher Stephane <seicher@compassion.ch>
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    attendance_day_id = fields.Many2one(comodel_name='hr.attendance.day',
                                        string='Attendance day',
                                        readonly=True)

    due_hours = fields.Float(related='attendance_day_id.due_hours')
    total_attendance = fields.Float(
        related='attendance_day_id.total_attendance')
    has_linked_change_day_request = fields.Boolean(
        related='attendance_day_id.has_linked_change_day_request')

    ##########################################################################
    #                               ORM METHODS                              #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ If the corresponding attendance day doesn't exist a new one is
        created"""
        new_record = super(HrAttendance, self).create(vals)
        att_check_in_date = fields.Date.from_string(vals['check_in'])
        attendance_day = self.env['hr.attendance.day'].search([
            ('employee_id', '=', vals['employee_id']),
            ('date', '=', att_check_in_date)
        ])
        if attendance_day:
            new_record.attendance_day_id = attendance_day
            # todo: find better solution
            new_record.attendance_day_id.compute_breaks()

        else:
            self.env['hr.attendance.day'].create({
                'employee_id': vals['employee_id'],
                'date': att_check_in_date
            })
        return new_record

    @api.multi
    def write(self, vals):
        for att in self:
            # Check if only the date of check_in has change and thus change the
            # attendance_day
            check_in_date = fields.Date.from_string(att.check_in)

            if 'check_in' in vals:
                check_in = fields.Date.from_string(vals['check_in'])
                # the check_in_date has change
                if check_in_date != check_in:
                    attendance_day = self.env['hr.attendance.day'].search([
                        ('employee_id', '=', att.employee_id.id),
                        ('date', '=', check_in)])
                    vals['attendance_day_id'] = attendance_day.id

            ret = super(HrAttendance, self).write(vals)

            if 'check_in' in vals or 'check_out' in vals:
                if 'no_compute_break' not in vals:
                    self.attendance_day_id.compute_breaks()

            return ret
