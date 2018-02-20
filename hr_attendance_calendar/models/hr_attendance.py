# -*- coding: utf-8 -*-
# Copyright (C) 2016 Coninckx David (Open Net Sarl)
# Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# @author: Stéphane Eicher <seicher@compassion.ch>

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # New fields --------------------------------------------------------------
    attendance_day_id = fields.Many2one(comodel_name='hr.attendance.day',
                                        string="Attendance day",
                                        readonly=True)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create(self, vals):
        new_record = super(HrAttendance, self).create(vals)
        att_check_in_date = fields.Date.from_string(vals['check_in'])
        attendance_day = self.env['hr.attendance.day'].search([
            ('employee_id', '=', vals['employee_id']),
            ('date', '=', att_check_in_date)
        ])
        if attendance_day:
            new_record.attendance_day_id = attendance_day

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
                if check_in_date != check_in:
                    attendance_day = self.env['hr.attendance.day'].search([
                        ('employee_id', '=', vals['employee_id']),
                        ('date', '=', check_in)])
                    vals['attendance_day_id'] = attendance_day

            super(HrAttendance, self).write(vals)

            if 'check_in' in vals or 'check_out' in vals:
                self.attendance_day_id.compute_breaks()

            return
