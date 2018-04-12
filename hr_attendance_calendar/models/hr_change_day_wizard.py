from odoo import models, fields, api, exceptions
import datetime


class ChangeDayDWizard(models.TransientModel):
    _name = 'hr.change.day.wizard'

    test = fields.Char('hello world')

    @api.multi
    def go_to_step2(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.change.day.wizard.step2',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'data': self.get_next_due_hours()}
        }

    @api.multi
    def get_next_due_hours(self):
        employee_id = self.env['res.users'].browse(self._uid).employee_ids
        employee_id.ensure_one()

        date_from = datetime.date.today()
        date_to = date_from

        while date_to.weekday() != 6:
            date_to += datetime.timedelta(1)
        date_to += datetime.timedelta(7)

        att_day = self.env['hr.attendance.day']
        att_day_created = []
        current_date = date_from

        while current_date <= date_to:
            already_exist = att_day.search([
                ('employee_id', '=', employee_id.id),
                ('date', '=', current_date)
            ])
            if not already_exist:
                att_day_created.append(att_day.create({
                    'employee_id': employee_id.id,
                    'date': current_date,
                }))
            current_date += datetime.timedelta(days=1)

        next_att_days = att_day.search(
            [('date', '>', date_from), ('date', '<=', date_to)])

        dates = next_att_days.mapped('date')
        due_hours = next_att_days.mapped('due_hours')

        data = dict()
        for index, date in enumerate(dates):
            #  only get days with due hours
            if due_hours[index] != 0:
                data[date] = due_hours[index]

        #  delete created att_days
        unlinked = [x.unlink() for x in att_day_created].count(False) == 0

        if unlinked:
            return data


class ChangeDayWizardStep2(models.TransientModel):
    _name = 'hr.change.day.wizard.step2'

    test = fields.Char('hello world')
    dates = fields.Selection(selection='_compute_dates')

    @api.multi
    def _compute_dates(self):
        if 'data' in self._context:
            return [(k, v) for k, v in self._context['data'].items()]
        return [('default', 'no valid date')]

    @api.multi
    def change_due_hours(self):
        employee_id = self.env['res.users'].browse(self._uid).employee_ids
        employee_id.ensure_one()

        day1 = {
            'employee_id': employee_id.id,
            'date': datetime.date.today(),
            'forced_due_hours': self._context['data'][self.dates]
        }
        day2 = {
            'employee_id': employee_id.id,
            'date': self.dates,
            'forced_due_hours': 0
        }
        forced_due_hours = self.env['hr.forced.due.hours']

        for day in [day1, day2]:
            domain = [('employee_id', '=', employee_id.id),
                      ('date', '=', day['date'])]

            existing = forced_due_hours.search(domain)
            if len(existing) == 1:
                existing.unlink()

            forced_due_hours.create(day)

            # recompute due hours after forced hour creation
            att_days = self.env['hr.attendance.day'].search(domain)
            for att_day in att_days:
                att_day.recompute_due_hours()
