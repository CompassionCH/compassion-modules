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
from datetime import timedelta

import datetime

from openerp import models, fields, api, _
from openerp.exceptions import UserError


class CompassionReservation(models.Model):

    _name = 'compassion.reservation'
    _description = 'Project Reservation'
    _inherit = ['compassion.abstract.hold', 'mail.thread']
    _rec_name = 'reservation_id'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    reservation_id = fields.Char(readonly=True)
    reservation_type = fields.Selection([
        ('project', 'Project reservation'),
        ('child', 'Child reservation')
    ], required=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('active', "Active"),
        ('expired', "Expired")],
        readonly=True, default='draft', track_visibility='onchange')
    icp_id = fields.Many2one('compassion.project', 'Project')
    child_id = fields.Many2one('compassion.child', 'Child', domain=[
        ('global_id', '!=', False), ('hold_id', '=', False)
    ])
    child_global_id = fields.Char(
        compute='_compute_child_global_id',
        inverse='_inverse_child_global_id', store=True
    )
    campaign_event_identifier = fields.Char()
    expiration_date = fields.Datetime(
        'Hold expiration date', track_visibility='onchange')
    reservation_expiration_date = fields.Date(
        required=True, track_visibility='onchange',
        default=lambda s: s._default_expiration_date())
    is_reservation_auto_approved = fields.Boolean(default=True)
    number_of_beneficiaries = fields.Integer(track_visibility='onchange')
    number_reserved = fields.Integer()

    _sql_constraints = [
        ('reservation_id', 'unique(reservation_id)',
         'The Reservation already exists in database.'),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('child_id')
    def _compute_child_global_id(self):
        for reservation in self.filtered('child_id'):
            reservation.child_global_id = reservation.child_id.global_id

    @api.multi
    def _inverse_child_global_id(self):
        for reservation in self.filtered('child_global_id'):
            child = self.env['compassion.child'].search([
                ('global_id', '=', reservation.child_global_id)])
            if not child:
                # Create child (not available yet to us)
                child = self.env['compassion.child'].create({
                    'global_id': reservation.child_global_id,
                })
            reservation.child_id = child

    def _default_expiration_date(self):
        days_reservation = self.env[
            'availability.management.settings'].get_param(
            'reservation_duration')
        dt = timedelta(days=days_reservation)
        expiration = datetime.date.today() + dt
        return fields.Date.to_string(expiration)

    ##########################################################################
    #                             ORM METHODS                                #
    ##########################################################################
    @api.multi
    def write(self, vals):
        res = super(CompassionReservation, self).write(vals)
        sync_fields = [
            'reservation_expiration_date', 'expiration_date',
            'number_of_beneficiaries', 'primary_owner']
        sync = False
        for field in sync_fields:
            if field in vals:
                sync = True
                break
        if sync:
            messages = self.filtered(
                lambda r: r.state == 'active')._handle_reservation()
            messages.with_context(async_mode=False).process_messages()
            failed = messages.filtered(lambda m: m.state == 'failure')
            if failed:
                raise UserError(
                    "\n\n".join(failed.mapped('failure_reason'))
                )
        return res

    @api.multi
    def unlink(self):
        active = self.filtered(lambda r: r.state == 'active')
        draft = self.filtered(lambda r: r.state == 'draft')
        active.cancel_reservation()
        super(CompassionReservation, draft).unlink()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def check_reservation_validity(self):
        expired_reservations = self.env['compassion.reservation'].search([
            ('expiration_date', '<',
             fields.Datetime.now())
        ])
        expired_reservations.write({'state': 'expired'})
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def send_reservation(self):
        messages = self._handle_reservation()
        messages.with_context(async_mode=False).process_messages()
        for i in range(0, len(messages)):
            if messages[i].state == 'success':
                self[i].state = 'active'
            else:
                self[i].message_post(
                    messages[i].failure_reason,
                    _("Reservation failed")
                )
                messages[i].unlink()
        return True

    @api.multi
    def cancel_reservation(self):
        messages = self._handle_reservation(cancel=True)
        messages.with_context(async_mode=False).process_messages()
        for i in range(0, len(messages)):
            if messages[i].state == 'success':
                self[i].state = 'expired'
            else:
                messages[i].unlink()
        return True

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
            'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.onchange('reservation_expiration_date')
    def onchange_expiration_date(self):
        if not self.reservation_expiration_date:
            return
        expiration = fields.Date.from_string(self.reservation_expiration_date)
        days_on_hold = self.env['availability.management.settings'].get_param(
            'reservation_hold_duration')
        dt = timedelta(days=days_on_hold)
        self.expiration_date = fields.Date.to_string(expiration + dt)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _handle_reservation(self, cancel=False):
        messages = self.env['gmc.message.pool']
        action = False
        for reservation in self:
            if reservation.reservation_type == 'child':
                if cancel:
                    action = self.env.ref(
                        'child_compassion.cancel_reservation_child')
                else:
                    action = self.env.ref(
                        'child_compassion.beneficiary_reservation')
            elif reservation.reservation_type == 'project':
                if cancel:
                    action = self.env.ref(
                        'child_compassion.cancel_reservation')
                else:
                    action = self.env.ref(
                        'child_compassion.create_reservation')
            messages += messages.create({
                'action_id': action.id,
                'object_id': reservation.id,
                'child_id': reservation.child_id.id,
            })

        return messages
