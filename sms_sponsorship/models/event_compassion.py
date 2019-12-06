##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields
from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.queue_job.job import job
from .sms_child_request import DEFAULT_MAX_AGE

# How many children are put on hold for SMS sponsorships in case we have
# no sponsorships planned
SMS_MIN_HOLD_NUMBER = 50

_logger = logging.getLogger(__name__)


class EventCompassion(models.Model):

    _inherit = 'crm.event.compassion'

    accepts_sms_booking = fields.Boolean(
        'Enable SMS Sponsorships',
        help="If checked, children will be allocated especially for "
             "sponsorships made with SMS requests.")
    sms_number_hold_target = fields.Integer(
        compute='_compute_sms_number_hold_target'
    )
    initial_sms_allocation_done = fields.Boolean()

    @api.multi
    def _compute_sms_number_hold_target(self):
        for event in self:
            event.sms_number_hold_target = max(event.number_allocate_children,
                                               SMS_MIN_HOLD_NUMBER)

    @api.model
    def hold_children_for_sms_cron(self):
        in_one_day = datetime.now() + relativedelta(days=1)
        events = self.search([
            ('accepts_sms_booking', '=', True),
            ('start_date', '<=', fields.Datetime.to_string(in_one_day)),
            ('start_date', '>=', fields.Datetime.now()),
            ('initial_sms_allocation_done', '=', False)
        ])
        events.hold_children_for_sms()
        events.write({'initial_sms_allocation_done': True})
        return True

    @api.multi
    @job
    def hold_children_for_sms(self, force_hold_number=None):
        """ Put children on hold for an event that accepts SMS sponsorships
        :param force_hold_number: Used to set the number of children to reserve
                                  If not set, will use the sms hold target
        :return: True
        """
        for event in self:
            _logger.info("Starting to put children on hold for event {}"
                         .format(event.name))
            take = force_hold_number or event.sms_number_hold_target
            childpool_search = self.env['compassion.childpool.search'].create({
                'take': take,
                'max_age': DEFAULT_MAX_AGE
            })
            childpool_search.with_context(skip_value=1000).do_search()
            expiration = fields.Datetime.from_string(event.end_date) + \
                relativedelta(days=2)
            self.env['child.hold.wizard'].with_context(
                active_id=childpool_search.id).create({
                    'type': HoldType.CONSIGNMENT_HOLD.value,
                    'expiration_date': fields.Datetime.to_string(expiration),
                    'primary_owner': self.env.uid,
                    'event_id': event.id,
                    'campaign_id': event.campaign_id.id,
                    'ambassador': event.user_id.partner_id.id or
                    self.env.user.partner_id.id,
                    'channel': 'sms',
                    'source_code': 'automatic_sms_reservation_for_event',
                    'return_action': 'view_holds'
                }).send()
            _logger.info("{} children put back in event sms pool".format(take))
        return True
