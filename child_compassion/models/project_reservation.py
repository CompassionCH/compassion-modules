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

from openerp import models, fields


class ProjectReservation(models.Model):

    _name = 'icp.reservation'
    _description = 'Project Reservation'

    reservation_id = fields.Char()
    channel_name = fields.Char()
    icp_id = fields.Many2one(
        'compassion.project', 'Project', required=True
    )
    campaign_event_identifier = fields.Char()
    expiration_date = fields.Date(required=True)
    hold_expiration_date = fields.Datetime(required=True)
    hold_yield_rate = fields.Integer()
    is_reservation_auto_approved = fields.Boolean(required=True)
    number_of_beneficiaries = fields.Integer(required=True)
    primary_owner = fields.Char(required=True)
    secondary_owner = fields.Char()
