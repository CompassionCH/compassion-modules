# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, exceptions, fields, models, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class hr_planning_day_move_request(models.Model):
    ''' Add possibility to create request to modify the planning
        - Move a planning day
        - Create a new planning day
        Requests needed to be approved.
        Request can be created or approved in this cases only:
        - An employee does not work twice a day
        - An employee move a working day only
        - An employee cannot add a working day during his/her holiday
    '''
    _name = "hr.planning.day.move.request"

    def _employee_get(self):
        return self.env.user.id

    name = fields.Char(
        _('Name'), required=True, states={'validate': [('readonly', True)]})
    old_date = fields.Date(
        _('Old date'), states={'validate': [('readonly', True)]})
    new_date = fields.Date(
        _('New date'), required=True,
        states={'validate': [('readonly', True)]})
    hour_from = fields.Float(
        _('From'), default=8, states={'validate': [('readonly', True)]})
    hour_to = fields.Float(
        _('To'), default=17, states={'validate': [('readonly', True)]})
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', default=_employee_get, required=True,
        states={'validate': [('readonly', True)]})
    state = fields.Selection(
        [('to_approve', 'To Approve'), ('validate', 'Approved')],
        'Status', default='to_approve', track_visibility="onchange",
        readonly=True)
    type = fields.Selection(
        [('add', 'Add'), ('move', 'Move')], _('Type'), required=True,
        states={'validate': [('readonly', True)]})

    @api.multi
    def create(self, vals):
        # Move request
        for move_requ in self:
            if vals['type'] == 'move':
                # Check if this employee is working this day
                if (move_requ._check_is_working(
                        vals['employee_id'], vals['old_date'])):
                    return super(hr_planning_day_move_request,
                                 self).create(vals)
                # Check if the move will have no effect
                elif vals['old_date'] == vals['new_date']:
                    raise exceptions.Warning(_('Warning'),
                                             _(u'You chose the same date'))
                else:
                    employee_name = self.env['hr.employee'].browse(
                        vals['employee_id']).name
                    raise exceptions.Warning(
                        _('Warning'),
                        _(u'{} does not work this day : {}').format(
                            employee_name, vals['old_date'])
                    )
            # Add request
            else:
                vals['old_date'] = False
                return super(hr_planning_day_move_request, self).create(vals)

    def write(self, vals):
        if 'type' in vals:
            if vals['type'] == 'add':
                vals['old_date'] = False
        return super(hr_planning_day_move_request, self).write(vals)

    def _check_is_working(self, employee_id, date):
        planning_day_obj = self.env['hr.planning.day']
        planning_days = planning_day_obj.search(
            [('employee_id', '=', employee_id)])

        # Find in the planning day
        for planning_day in planning_days:
            if (datetime.strptime(
                planning_day.start_date, DTF).date() ==
                    datetime.strptime(date, DF).date()):
                return True

        return False

    # Approve a request
    @api.multi
    def approve(self, cr, uid, ids, context=None):
        self.write({'state': 'validate'})
        employee_ids = list()

        for move_request in self:
            employee_ids.append(move_request.employee_id.id)
            # Avoid to approve a request if the employee is already working
            if(move_request._check_is_working(
                    move_request.employee_id.id,
                    move_request.new_date)):
                raise exceptions.Warning(
                    _('Warning'),
                    _(u'{} already works this day : {}').format(
                        move_request.employee_id.name,
                        move_request.new_date)
                )
        self.env['hr.planning.wizard'].generate(employee_ids)
        return True

    # Refuse a request
    @api.multi
    def refuse(self, cr, uid, ids, context=None):
        self.write({'state': 'to_approve'})
        employee_ids = [move_request.employee_id.id
                        for move_request in self]
        self.env['hr.planning.wizard'].generate(employee_ids)
        return True

    # Delete a request
    @api.multi
    def unlink(self, cr, uid, ids, context=None):
        employee_ids = [move_request.employee_id.id
                        for move_request in self]
        res = super(hr_planning_day_move_request, self).unlink()
        self.env['hr.planning.wizard'].generate(employee_ids)
        return res
