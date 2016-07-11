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


class ProjectReservation(models.Model):

    _name = 'icp.reservation'
    _description = 'Project Reservation'

    name = fields.Char(required=True)
    beneficiary_global_id = fields.Char()
    reservation_id = fields.Char()
    channel_name = fields.Char()
    icp_id = fields.Many2one(
        'compassion.project', 'Project', required=True
    )
    campaign_event_identifier = fields.Char()
    expiration_date = fields.Date(required=True)
    hold_expiration_date = fields.Datetime(required=True)
    hold_yield_rate = fields.Integer()
    is_reservation_auto_approved = fields.Boolean(default=True)
    number_of_beneficiaries = fields.Integer(required=True)
    primary_owner = fields.Char(required=True)
    secondary_owner = fields.Char()
    active = fields.Boolean(default=True, readonly=True)

    @api.model
    def create(self, vals):
        res = super(ProjectReservation, self).create(vals)
        self.handle_reservation('child_compassion.create_reservation', res)
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

    @api.model
    def process_commkit(self, commkit_data):
        # TODO Implement
        return False

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
