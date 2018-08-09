# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields
from odoo.addons.child_compassion.models.compassion_hold import HoldType


class EventCompassion(models.Model):

    _inherit = 'crm.event.compassion'

    accepts_sms_booking = fields.Boolean('Accepts SMS booking')

    @api.model
    def hold_children_for_sms(self):
        in_one_day = datetime.now() + relativedelta(days=1)
        for event in self.search([
            ('accepts_sms_booking', '=', True),
            ('start_date', '<=', fields.Datetime.to_string(in_one_day))
        ]):
            childpool_search = self.env['compassion.childpool.search'].create({
                # Take 20% of planned sponsorships
                'take': int(event.planned_sponsorships * 0.2) or 3,
            })
            childpool_search.rich_mix()
            expiration = fields.Datetime.from_string(event.end_date) + \
                relativedelta(days=1)
            self.env['child.hold.wizard'].with_context(
                active_id=childpool_search.id).create({
                    'type': HoldType.CONSIGNMENT_HOLD.value,
                    'expiration_date': fields.Datetime.to_string(expiration),
                    'primary_owner': self.env.uid,
                    'event_id': event.id,
                    'campaign_id': event.campaign_id.id,
                    'ambassador': event.user_id.partner_id.id or self.env.uid,
                    'channel': 'sms',
                    'source_code': 'automatic_sms_reservation_for_event',
                    'return_action': 'view_holds'
                }).send()
        return True
