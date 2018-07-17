# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import re

logger = logging.getLogger(__name__)


class CompassionHold(models.Model):

    _inherit = 'compassion.hold'

    booked_by_phone_number = fields.Char()
    booked_by_sms_at = fields.Datetime(required=False)

    @api.multi
    def book_by_sms(self, phone_number):
        self.ensure_one()
        assert re.match(r'\+\d+', phone_number), \
            "The phone number do not match the international format"
        assert not self.event_id or self.event_id.accepts_sms_booking, \
            "SMS booking isn't supported for this event"
        if self.booked_by_phone_number:
            raise UserError(_('Child already booked by {}'
                            .format(self.booked_by_phone_number)))
        self.booked_by_phone_number = phone_number
        self.booked_by_sms_at = fields.Datetime.now()

    @api.multi
    def release_sms_booking(self):
        self.ensure_one()
        self.booked_by_phone_number = None
        self.booked_by_sms_at = None

    @api.multi
    def generate_url_of_next_step(self):
        self.ensure_one()
        return 'sms-sponsorship/{}'.format(self.id)
