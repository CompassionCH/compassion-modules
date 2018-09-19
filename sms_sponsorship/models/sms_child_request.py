# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import random

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.base_phone.fields import Phone
from odoo.addons.child_compassion.models.compassion_hold import HoldType

# By default, don't propose children older than this
DEFAULT_MAX_AGE = 12

_logger = logging.getLogger(__name__)


class SmsChildRequest(models.Model):
    _name = 'sms.child.request'
    _inherit = 'mail.thread'
    _description = 'SMS Child request'
    _rec_name = 'child_id'
    _order = 'date desc'

    sender = Phone(required=True, partner_field='partner_id',
                   country_field='country_id')
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    full_url = fields.Char(compute='_compute_full_url')
    step1_url_id = fields.Many2one('link.tracker')
    step1_url = fields.Char('Step 1 URL', related='step1_url_id.short_url')
    step2_url_id = fields.Many2one('link.tracker')
    step2_url = fields.Char('Step 2 URL', related='step2_url_id.short_url')
    state = fields.Selection([
        ('new', 'Request received'),
        ('child_reserved', 'Child reserved'),
        ('step1', 'Step 1 completed'),
        ('step2', 'Step 2 completed'),
        ('expired', 'Request expired')
    ], default='new', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Partner')
    country_id = fields.Many2one(
        'res.country', related='partner_id.country_id', readonly=True)
    child_id = fields.Many2one(
        'compassion.child', 'Child', ondelete='set null')
    hold_id = fields.Many2one('compassion.hold', related='child_id.hold_id')
    event_id = fields.Many2one(
        'crm.event.compassion', 'Event',
        domain=[('accepts_sms_booking', '=', True)],
        compute='_compute_event', inverse='_inverse_event', store=True
    )
    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship')
    sponsorship_confirmed = fields.Boolean('Sponsorship confirmed')
    lang_code = fields.Char('Language', required=True)

    # Filter criteria made by sender
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    min_age = fields.Integer(size=2)
    max_age = fields.Integer(size=2, default=DEFAULT_MAX_AGE)
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field Office')

    new_partner = fields.Boolean('New partner ?',
                                 help="is true if partner was created when "
                                      "sending sms", default=False)
    is_trying_to_fetch_child = fields.Boolean(
        help="This is set to true when a child is currently being fetched. "
             "It prevents to fetch multiple children.")
    sms_reminder_sent = fields.Boolean(default=False)
    has_filter = fields.Boolean(compute='_compute_has_filter')

    @api.multi
    def _compute_full_url(self):
        for request in self:
            if request.state == 'step1':
                request.full_url = request.step2_url
            else:
                request.full_url = request.step1_url

    @api.multi
    @api.depends('date')
    def _compute_event(self):
        limit_date = datetime.today() - relativedelta(days=7)
        for request in self.filtered('date'):
            event_id = self.env['crm.event.compassion'].search([
                ('accepts_sms_booking', '=', True),
                ('start_date', '<=', request.date),
                ('start_date', '>=', fields.Datetime.to_string(limit_date))
            ], order='start_date desc', limit=1)
            # event_id is None if start_date of most recent event is>1 week old
            request.event_id = event_id

    def _inverse_event(self):
        # Allows to manually set an event
        return True

    @api.multi
    def _compute_has_filter(self):
        for request in self:
            request.has_filter = request.gender or request.min_age or \
                request.field_office_id or (request.max_age and
                                            request.max_age != DEFAULT_MAX_AGE)

    @api.model
    def create(self, vals):
        if 'partner_id' not in vals:
            # Try to find a matching partner given phone number
            phone = vals.get('sender')
            partner_obj = self.env['res.partner']
            partner = partner_obj.search([('mobile', 'like', phone)]) or \
                partner_obj.search([('phone', 'like', phone)])
            if partner and len(partner) == 1:
                vals['partner_id'] = partner.id
                vals['lang_code'] = partner.lang
        request = super(SmsChildRequest, self).create(vals)
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url') + '/'
        request.write({
            'step1_url_id': self.env['link.tracker'].sudo().create({
                'url': base_url + request.lang_code +
                '/sms_sponsorship/step1/' + str(request.id),
            }).id,
            'is_trying_to_fetch_child': True
        })
        # Directly commit for the job to work
        self.env.cr.commit()  # pylint: disable=invalid-commit
        request.with_delay(priority=5).reserve_child()
        return request

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        phone = self.partner_id.mobile or self.partner_id.phone
        if phone:
            self.sender = phone
        self.lang_code = self.partner_id.lang

    @api.multi
    def change_child(self):
        """ Release current child and take another."""
        self.hold_id.write({'sms_request_id': False})
        self.write({
            'state': 'new',
            'child_id': False,
            'is_trying_to_fetch_child': True
        })
        return self.reserve_child()

    @api.multi
    def cancel_request(self):
        self.hold_id.write({'sms_request_id': False})
        return self.write({
            'state': 'expired',
            'child_id': False
        })

    @job(default_channel='root.sms_request')
    @related_action(action='related_action_sms_request')
    def reserve_child(self):
        """Finds a child for SMS sponsorship service.
        Try to fetch a child in the event allocation pool or
        put a new child on hold for the sms request.
        """
        self.ensure_one()
        child_fetched = None
        if self.event_id:
            child_fetched = self._take_child_from_event()
        if not child_fetched:
            child_fetched = self.take_child_from_childpool()
        self.is_trying_to_fetch_child = False
        return child_fetched

    def complete_step1(self, sponsorship_id):
        """
        Create short link for step2, send confirmation to partner.
        :param sponsorship_id: id of the new sponsorship.
        :return: True
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url') + '/'
        self.write({
            'sponsorship_id': sponsorship_id,
            'state': 'step1',
            'step2_url_id': self.env['link.tracker'].sudo().create({
                'url': base_url + self.lang_code + '/sms_sponsorship/step2/' +
                str(sponsorship_id)
            }).id
        })
        self.partner_id.sms_send_step1_confirmation(self)
        return True

    def complete_step2(self):
        """
        Send confirmation to partner and update state.
        :return: True
        """
        self.ensure_one()
        self.partner_id.sms_send_step2_confirmation(self)
        return self.write({'state': 'step2'})

    def take_child_from_childpool(self):
        try:
            childpool_search = self.env[
                'compassion.childpool.search'].create({
                    'take': 1,
                    'gender': self.gender,
                    'min_age': self.min_age,
                    'max_age': self.max_age,
                    'field_office_ids': [(6, 0,
                                          self.field_office_id.ids or [])]
                })
            childpool_search.do_search()
            # Request is valid two days, reminder is sent one day after
            expiration = datetime.now() + relativedelta(days=2)
            result_action = self.env['child.hold.wizard'].with_context(
                active_id=childpool_search.id, async_mode=False).create({
                    'type': HoldType.E_COMMERCE_HOLD.value,
                    'expiration_date': fields.Datetime.to_string(expiration),
                    'primary_owner': self.env.uid,
                    'event_id': self.event_id.id,
                    'campaign_id': self.event_id.campaign_id.id,
                    'ambassador': self.event_id.user_id.partner_id.id or
                    self.env.uid,
                    'channel': 'sms',
                    'source_code': 'sms_sponsorship',
                    'return_action': 'view_holds'
                }
            ).send()
            child_hold = self.env['compassion.hold'].browse(
                result_action['domain'][0][2])
            child_hold.sms_request_id = self.id
            if child_hold.state == 'active':
                self.write({
                    'child_id': child_hold.child_id.id,
                    'state': 'child_reserved'
                })
                _logger.info("SMS child directly taken from global pool")
                return True
            else:
                _logger.error("SMS child couldn't be put on hold from global "
                              "pool")
                return False
        except:
            _logger.error("Error during SMS child reservation", exc_info=True)
            self.env.cr.rollback()
            self.env.invalidate_all()
            return False
        finally:
            self.is_trying_to_fetch_child = False

    def _take_child_from_event(self):
        """ Search in the allocated children for the event.
        """
        event_holds = self.event_id.hold_ids.filtered(
            lambda h: h.state == 'active' and h.channel == 'sms' and not
            h.sms_request_id)
        available_hold = None
        if self.has_filter:
            for child_hold in random.shuffle(event_holds):
                if self.check_hold_child_parameters(child_hold):
                    available_hold = child_hold
        else:
            available_hold = random.choice(event_holds)
        if available_hold:
            self.write({
                'child_id': available_hold.child_id.id,
                'state': 'child_reserved'
            })
            available_hold.sms_request_id = self.id
            # Put a new child in event buffer
            self.event_id.with_delay().hold_children_for_sms(1)
            _logger.info("SMS child taken from event pool")
            return True
        return False

    def check_hold_child_parameters(self, child_hold):
        if child_hold.child_id.gender == self.gender and \
            child_hold.child_id.min_age == self.min_age \
            and child_hold.child_id.max_age == self.max_age \
                and child_hold.child_id.country_id == self.country_id:
                    return True
        else:
            return False

    @api.multi
    def send_step1_reminder(self):
        """ Can be extended to use a SMS API and send a reminder to user. """
        self.ensure_one()
        self.write({'sms_reminder_sent': True})

    @api.model
    def sms_reminder_cron(self):
        """
        CRON job that sends SMS reminders to people that didn't complete
        step 1.
        :return: True
        """
        sms_requests = self.search([
            ('sms_reminder_sent', '=', False),
            ('date', '<', fields.Date.today()),
            ('state', 'in', ['new', 'child_reserved']),
        ])
        for request in sms_requests:
            request.with_context(lang=request.lang_code).send_step1_reminder()
        return True
