# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class HrForcedDueHours(models.Model):
    _name = 'hr.forced.due.hours'
    _order = 'date'

    _sql_constraints = [('unique_due_hours', 'unique(date, employee_id)',
                         'This "Forced due hour" already exists')]

    employee_id = fields.Many2one('hr.employee',
                                  string='Employee', required=True)
    date = fields.Date('Date', required=True)
    forced_due_hours = fields.Float('Forced due hours', required=True)

    @api.model
    def recompute_due_hours(self, employee_id, date):
        return self.env['hr.attendance.day'].search(
            [('employee_id', '=', employee_id),
             ('date', '=', date)]).recompute_due_hours()

    @api.multi
    def write(self, vals):
        for record in self:
            old_vals = dict()
            for field in ['employee_id', 'date', 'forced_due_hours']:
                old_vals[field] = getattr(record, field)

            super(HrForcedDueHours, record).write(vals)

            record.recompute_due_hours(
                old_vals['employee_id'].id, old_vals['date'])
            record.recompute_due_hours(record.employee_id.id, record.date)

    @api.multi
    def unlink(self):
        length = len(self)
        employee_ids = [0]*length
        dates = [0]*length
        for i in range(length):
            employee_ids[i] = self[i].employee_id.id
            dates[i] = self[i].date

        super(HrForcedDueHours, self).unlink()
        for i in range(length):
            self.recompute_due_hours(employee_ids[i], dates[i])


class HrChangeDayRequest(models.Model):
    _inherit = 'mail.thread'
    _name = 'hr.change.day.request'

    user_id = fields.Many2one('res.users', string='Manager',
                              readonly=True,
                              track_visibility='onchange')

    day1_id = fields.Many2one('hr.forced.due.hours')
    day2_id = fields.Many2one('hr.forced.due.hours')
    employee_id = fields.Many2one('hr.employee', related='day1_id.employee_id')

    date1 = fields.Date('Date 1', related='day1_id.date')
    date2 = fields.Date('Date 2', related='day2_id.date')
    forced1 = fields.Float('Hours 1', related='day1_id.forced_due_hours')
    forced2 = fields.Float('Hours 2', related='day2_id.forced_due_hours')

    forced = fields.Char('Hours changed', compute='_compute_hours')

    @api.model
    def create(self, vals):
        forced_due_hours = self.env['hr.forced.due.hours']

        day1 = {
            'employee_id': vals['employee_id'],
            'date': vals['date1'],
            'forced_due_hours': vals['forced1']
        }
        day2 = {
            'employee_id': vals['employee_id'],
            'date': vals['date2'],
            'forced_due_hours': vals['forced2']
        }

        day1_id = forced_due_hours.create(day1)
        day2_id = forced_due_hours.create(day2)

        res = super(HrChangeDayRequest, self).create({
            'day1_id': day1_id.id,
            'day2_id': day2_id.id,
            'user_id': vals['user_id']
        })

        for d in [day1, day2]:
            forced_due_hours.recompute_due_hours(d['employee_id'], d['date'])

        return res

    @api.multi
    def unlink(self):
        for request in self:
            request.day1_id.unlink()
            request.day2_id.unlink()

        super(HrChangeDayRequest, self).unlink()

    @api.multi
    def _compute_hours(self):
        for h in self:
            h.forced = h.forced2 if h.forced != 0 else h.forced1
