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
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.base_phone.fields import Phone
from odoo.addons.child_compassion.models.compassion_hold import HoldType


class SmsChildRequest(models.Model):
    _name = 'sms.child.request'
    _inherit = 'mail.thread'
    _description = 'SMS Child request'
    _rec_name = 'child_id'
    _order = 'date desc'

    sender = Phone(required=True, partner_field='partner_id',
                   country_field='country_id')
    date = fields.Datetime(required=True, default=fields.Datetime.now())
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

    # Filter criteria made by sender
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    min_age = fields.Integer(size=2)
    max_age = fields.Integer(size=2)
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field Office')

    new_partner = fields.Boolean('New partner ?',
                                 help="is true if partner was created when "
                                      "sending sms", default=False)
    is_trying_to_fetch_child = fields.Boolean(
        help="This is set to true when a child is currently being fetched. "
             "It prevents to fetch multiple children.")

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
        for request in self.filtered('date'):
            event_id = self.env['crm.event.compassion'].search([
                ('accepts_sms_booking', '=', True),
                ('start_date', '<=', fields.Datetime.to_string(request.date)),
                ('start_date', '>=', fields.Datetime.to_string(
                    datetime.today()) - datetime.timedelta(days=7))
            ], order='start_date desc', limit=1)
            # event_id is None if start_date of most recent event is>1 week old
            request.event_id = event_id

    def _inverse_event(self):
        # Allows to manually set an event
        return True

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
        request = super(SmsChildRequest, self).create(vals)
        lang = request.partner_id.lang or self.env.lang
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url') + '/'
        request.write({
            'step1_url_id': self.env['link.tracker'].sudo().create({
                'url': base_url + lang + '/sms_sponsorship/step1/' +
                       str(request.id),
            }).id,
            'is_trying_to_fetch_child': True
        })
        # Directly commit for the job to work
        self.env.cr.commit()  # pylint: disable=invalid-commit
        request.with_delay().reserve_child()
        return request

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        phone = self.partner_id.mobile or self.partner_id.phone
        if phone:
            self.sender = phone

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
        Put the child on hold for the sms request. If the hold request is
        not working, fallback to search a child already allocated for the
        event.
        """
        self.ensure_one()
        childpool_search = self.env['compassion.childpool.search'].create({
            'take': 1,
            'gender': self.gender,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'field_office_ids': [(6, 0, self.field_office_id.ids or [])]
        })
        if self.gender or self.min_age or self.max_age or \
            self.field_office_id:
            childpool_search.do_search()
        else:
            childpool_search.rich_mix()
        expiration = datetime.now() + relativedelta(minutes=15)
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
        self.is_trying_to_fetch_child = False
        if child_hold.state == 'active':
            self.write({
                'child_id': child_hold.child_id.id,
                'state': 'child_reserved'
            })
        else:
            self._take_child_from_event()
        return True

    def complete_step1(self, sponsorship_id):
        """
        Create short link for step2, send confirmation to partner.
        :param sponsorship_id: id of the new sponsorship.
        :return: True
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url')
        self.write({
            'sponsorship_id': sponsorship_id,
            'state': 'step1',
            'step2_url_id': self.env['link.tracker'].sudo().create({
                'url': base_url + '/sms_sponsorship/step2/' +
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

    def _take_child_from_event(self):
        """ Called in case we couldn't make a hold from global childpool.
        We will search if we have some children available for the sms service.
        """
        available_holds = self.event_id.hold_ids.filtered(
            lambda h: h.channel == 'sms' and not h.sms_request_id)
        if available_holds:
            available_holds[0].sms_request_id = self.id
            self.write({
                'child_id': available_holds[0].child_id.id,
                'state': 'child_reserved'
            })
