# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning


class ProjectReservation(models.Model):

    _name = 'icp.reservation'
    _description = 'Project Reservation'
    _inherit = 'compassion.abstract.hold'

    name = fields.Char(required=True)
    reservation_id = fields.Char()
    icp_id = fields.Many2one(
        'compassion.project', 'Project', required=True)
    child_id = fields.Many2one('compassion.child', 'Child', readonly=True)
    campaign_event_identifier = fields.Char()
    reservation_expiration_date = fields.Date(required=True)
    hold_expiration_date = fields.Datetime(related='expiration_date')
    is_reservation_auto_approved = fields.Boolean(default=True)
    number_of_beneficiaries = fields.Integer(required=True)
    active = fields.Boolean(default=True, readonly=True)

    _sql_constraints = [
        ('reservation_id', 'unique(reservation_id)',
         'The Reservation already exists in database.'),
    ]

    @api.model
    def check_reservation_validity(self):
        expired_reservations = self.env['icp.reservation'].search([
            ('expiration_date', '<',
             fields.Datetime.now())
        ])
        for reservation in expired_reservations:
            reservation.active = False
        return True

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.model
    def create(self, vals):
        res = super(ProjectReservation, self).create(vals)
        if vals.get('child_id') is None:
            action = 'child_compassion.create_reservation'
        else:
            action = 'child_compassion.beneficiary_reservation'
        self.handle_reservation(action, res)
        return res

    @api.multi
    def write(self, vals):
        res = super(ProjectReservation, self).write(vals)
        if not self.env.context.get('creating') and self.active:
            self.with_context(creating=False).handle_reservation(
                'child_compassion.create_reservation', res)
        return res

    @api.multi
    def unlink(self):
        self.cancel_reservation()
        return

    @api.multi
    def cancel_reservation(self):
        self.active = False
        self.handle_reservation('child_compassion.cancel_reservation')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current'
        }

    @api.multi
    def show_reserved_children(self):
        self.ensure_one()

        holds = self.env['compassion.hold'].search([
            ('reservation_id', '=', self.id)
        ])
        children_ids = holds.mapped('child_id.id')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'compassion.child',
            'domain': [('id', 'in', children_ids)],
            'view_mode': 'tree, form',
            'target': 'new',
        }

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def handle_reservation(self, action, res=False):
        message_obj = self.env['gmc.message.pool']

        action_id = self.env.ref(action).id
        object_id = res.id if type(res) is not bool else self.id
        message_vals = {
            'action_id': action_id,
            'object_id': object_id
        }
        pool = message_obj.with_context(async_mode=False,
                                        creating=True).create(message_vals)
        if pool.failure_reason:
            raise Warning("Reservation impossible", pool.failure_reason)
        return
