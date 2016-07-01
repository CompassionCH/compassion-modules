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
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.create_reservation').id

        message_vals = {
            'action_id': action_id,
            'object_id': res.id,
        }
        message_obj.with_context(async_mode=False).create(message_vals)
        return res

    @api.multi
    def unlink(self):
        message_obj = self.env['gmc.message.pool']
        action_id = self.env.ref('child_compassion.cancel_reservation').id

        self.active = False
        message_vals = {
            'action_id': action_id,
            'object_id': self.id
        }
        message_obj.with_context(async_mode=False).create(message_vals)
        return
