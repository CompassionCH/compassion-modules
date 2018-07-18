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
from odoo import models, api, fields
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.base_phone.fields import Phone


class SmsChildRequest(models.Model):
    _name = 'sms.child.request'
    _description = 'SMS Child request'
    _rec_name = 'child_id'
    _order = 'date desc'

    sender = Phone(required=True, partner_field='partner_id',
                   country_field='country_id')
    date = fields.Datetime(required=True, default=fields.Datetime.now())
    website_url = fields.Char(compute='_compute_website_url', store=True)
    full_url = fields.Char(compute='_compute_full_url')
    state = fields.Selection([
        ('new', 'Request received'),
        ('child_reserved', 'Child reserved'),
        ('step1', 'Step 1 completed'),
        ('step2', 'Step 2 completed'),
        ('expired', 'Request expired')
    ], default='new')
    partner_id = fields.Many2one('res.partner', 'Partner')
    country_id = fields.Many2one(
        'res.country', related='partner_id.country_id', readonly=True)
    child_id = fields.Many2one('compassion.child', 'Child')
    event_id = fields.Many2one(
        'crm.event.compassion', 'Event',
        domain=[('accepts_sms_booking', '=', True)],
        compute='_compute_event', inverse='_inverse_event', store=True
    )
    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship')

    # Filter criterias made by sender
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    min_age = fields.Integer(size=2)
    max_age = fields.Integer(size=2)
    field_office_ids = fields.Many2one(
        'compassion.field.office', 'Field Office')

    @api.multi
    def _compute_website_url(self):
        for request in self:
            request.website_url = '/sponsor-now/' + str(request.id)

    @api.multi
    def _compute_full_url(self):
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url')
        for request in self:
            request.full_url = base_url + request.website_url

    @api.multi
    @api.depends('date')
    def _compute_event(self):
        for request in self.filtered('date'):
            request.event_id = self.env['crm.event.compassion'].search([
                ('accepts_sms_booking', '=', True),
                ('start_date', '<=', request.date)
            ], limit=1)

    def _inverse_event(self):
        # Allows to manually set an event
        return True

    @api.model
    def create(self, vals):
        if 'partner_id' not in vals:
            # Try to find a matching partner given phone number
            phone = vals.get('sender')
            partner_obj = self.env['res.partner']
            partner = partner_obj.search([
                '|', ('mobile', 'like', phone),
                ('phone', 'like', phone)
            ])
            if partner and len(partner) == 1:
                vals['partner_id'] = partner.id
        request = super(SmsChildRequest, self).create(vals)
        # Directly commit for the job to work
        self.env.cr.commit()    # pylint: disable=invalid-commit
        request.with_delay().reserve_child()
        return request

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        phone = self.partner_id.mobile or self.partner_id.phone
        if phone:
            self.sender = phone

    @api.multi
    def change_child(self):
        """ Release current child and take another. TODO """
        # TODO Release
        if self.child_id:
            pass
        return self.reserve_child()

    @api.multi
    def cancel_request(self):
        # TODO release child
        if self.child_id:
            pass
        return self.write({
            'state': 'expired'
        })

    @job(default_channel='root.sms_request')
    @related_action(action='related_action_sms_request')
    def reserve_child(self):
        """
        Finds a child for the closest event with SMS service activated.
        Put the child on hold for the sms request. If the hold request is
        not working, fallback to search a child already allocated for the
        event.
        TODO
        """
        self.ensure_one()
        return self.write({
            'state': 'child_reserved',
            'child_id': False
        })
