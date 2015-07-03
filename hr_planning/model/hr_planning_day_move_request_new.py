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
import openerp
from openerp import api, models
from openerp.osv import orm, fields
from openerp.tools.translate import _
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

    def _employee_get(self, cr, uid, context=None):
        ids = self.pool.get('hr.employee').search(
            cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False

    name = openerp.fields.Char(
        _('Name'), required=True,
        states={'validate': [('readonly', True)]})
    old_date = openerp.fields.Date(
        _('Old date'),
        states={'validate': [('readonly', True)]})
    new_date = openerp.fields.Date(
        _('New date'), required=True,
        states={'validate': [('readonly', True)]})
    hour_from = openerp.fields.Float(
        _('From'), states={'validate': [('readonly', True)]})
    hour_to = openerp.fields.float(
        _('To'), states={'validate': [('readonly', True)]})
    employee_id = openerp.fields.Many2one(
        'hr.employee', 'Employee', required=True,
        states={'validate': [('readonly', True)]})
    state = openerp.fields.Selectionelection(
        [('to_approve', 'To Approve'), ('validate', 'Approved')],
        'Status', track_visibility="onchange", readonly=True)
    type = openerp.fields.Selection(
        [('add', 'Add'), ('move', 'Move')],
        _('Type'), required=True,
        states={'validate': [('readonly', True)]})

    # _columns = {
        # 'name': fields.char(
            # _('Name'), required=True,
            # states={'validate': [('readonly', True)]}),
        # 'old_date': fields.date(
            # _('Old date'),
            # states={'validate': [('readonly', True)]}),
        # 'new_date': fields.date(
            # _('New date'), required=True,
            # states={'validate': [('readonly', True)]}),
        # 'hour_from': fields.float(
            # _('From'), states={'validate': [('readonly', True)]}),
        # 'hour_to': fields.float(
            # _('To'), states={'validate': [('readonly', True)]}),
        # 'employee_id': fields.many2one(
            # 'hr.employee', 'Employee', required=True,
            # states={'validate': [('readonly', True)]}),
        # 'state': fields.selection(
            # [('to_approve', 'To Approve'), ('validate', 'Approved')],
            # 'Status', track_visibility="onchange", readonly=True),
        # 'type': fields.selection(
            # [('add', 'Add'), ('move', 'Move')],
            # _('Type'), required=True,
            # states={'validate': [('readonly', True)]}),
    # }
    _defaults = {
        'state': 'to_approve',
        'employee_id': _employee_get,
        'hour_from': 8,
        'hour_to': 17,
    }

    @api.model
    def create(self, vals):
        # Move request
        if vals['type'] == 'move':
            # Check if this employee is working this day
            if (self._check_is_working(vals['employee_id'], vals['old_date'])):
                return super(hr_planning_day_move_request, self).create(vals)
            # Check if the move will have no effect
            elif vals['old_date'] == vals['new_date']:
                raise orm.except_orm(_('Warning'),
                                     _(u'You chose the same date'))
            else:
                employee_name = self.env['hr.employee'].browse(
                    vals['employee_id']).name
                raise orm.except_orm(
                    _('Warning'),
                    _(u'{} does not work this day : {}').format(
                        employee_name, vals['old_date'])
                )
        # Add request
        else:
            vals['old_date'] = False
            return super(hr_planning_day_move_request, self).create(vals)

    @api.model
    def write(self, vals):
        if 'type' in vals:
            if vals['type'] == 'add':
                vals['old_date'] = False
        return super(hr_planning_day_move_request, self).write(vals)

    @api.model
    def _check_is_working(self, employee_id, date):
        planning_day_obj = self.pool.get('hr.planning.day')
        planning_day_ids = planning_day_obj.search(
            cr, uid, [('employee_id', '=', employee_id)], context=context)

        # Find in the planning day
        for planning_day in planning_day_obj.browse(
                cr, uid, planning_day_ids, context):
            if (datetime.strptime(
                planning_day.start_date, DTF).date() ==
                    datetime.strptime(date, DF).date()):
                return True

        return False

    # Approve a request
    def approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'validate'}, context)
        employee_ids = list()

        for move_request in self.browse(cr, uid, ids, context=context):
            employee_ids.append(move_request.employee_id.id)
            # Avoid to approve a request if the employee is already working
            if(self._check_is_working(
                    cr, uid,
                    move_request.employee_id.id,
                    move_request.new_date,
                    context)):
                raise orm.except_orm(
                    _('Warning'),
                    _(u'{} already works this day : {}').format(
                        move_request.employee_id.name,
                        move_request.new_date)
                )
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, employee_ids, context)
        return True

    # Refuse a request
    def refuse(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'to_approve'}, context)
        employee_ids = [move_request.employee_id.id
                        for move_request in self.browse(
                            cr, uid, ids, context)]
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, employee_ids, context)
        return True

    # Delete a request
    def unlink(self, cr, uid, ids, context=None):
        employee_ids = [move_request.employee_id.id
                        for move_request in self.browse(
                            cr, uid, ids, context)]
        res = super(hr_planning_day_move_request, self).unlink(
            cr, uid, ids, context)
        self.pool.get('hr.planning.wizard').generate(
            cr, uid, employee_ids, context)
        return res
