# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job, related_action
import logging

_logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    group_id = fields.Many2one(required=False)

    @api.model
    @job
    def create_sms_sponsorship(self, vals, partner, sms_child_request):
        """
        Creates sponsorship from REACT webapp data.
        :param vals: form values
        :param partner: res.partner record
        :param sms_child_request: sms.child.request record
        :return: True
        """
        if not partner:
            # Search for existing partner
            partner = self.env['res.partner'].search([
                ('firstname', 'ilike', vals['firstname']),
                ('lastname', 'ilike', vals['lastname']),
                ('email', '=', vals['email'])
            ])
            sms_child_request.partner_id = partner
        else:
            if not (partner.firstname == vals['firstname'] and
                    partner.lastname == vals['lastname'] and
                    partner.email == vals['email']):
                    partner = False

        if not partner:
            partner = self.env['res.partner'].create({
                'firstname': vals['firstname'],
                'lastname': vals['lastname'],
                'phone': vals['phone'],
                'email': vals['email'],
            })
            sms_child_request.new_partner = True
            sms_child_request.partner_id = partner

        # Create sponsorship
        lines = self._get_sponsorship_standard_lines()
        if not vals['sponsorship_plus']:
            lines = lines[:-1]
        sponsorship = self.create({
            'partner_id': partner.id,
            'correspondent_id': partner.id,
            'child_id': sms_child_request.child_id.id,
            'type': 'S',
            'contract_line_ids': lines,
            'medium_id': self.env.ref('sms_sponsorship.utm_medium_sms').id,
            'origin_id': sms_child_request.event_id.origin_id.id,
        })
        sponsorship.on_change_origin()
        sponsorship.with_delay().put_child_on_no_money_hold()
        partner.set_privacy_statement(origin='new_sponsorship')
        sms_child_request.complete_step1(sponsorship.id)
        return True

    @job(default_channel="root.sms_sponsorship")
    @related_action(action='related_action_finalize_form')
    def finalize_form(self, pay_first_month_ebanking):
        # validate sponsorship and send confirmation email
        sms_request = self.env['sms.child.request'].sudo().search([
            ('sponsorship_id.id', '=', self.id)
        ])
        # check if partner was created via the SMS request. new_partner
        # is set at True in recurring_contract in models
        if sms_request.new_partner:
            # send staff notification
            notify_ids = self.env['staff.notification.settings'].get_param(
                'new_partner_notify_ids')
            if notify_ids:
                self.message_post(
                    body=_("A new partner was created by SMS and needs a "
                           "manual confirmation"),
                    subject=_("New SMS partner"),
                    partner_ids=notify_ids,
                    type='comment',
                    subtype='mail.mt_comment',
                    content_subtype='plaintext'
                )
        else:
            self.signal_workflow('contract_validated')

        # if sponsor directly payed
        if pay_first_month_ebanking:
            # load payment view ? TODO
            _logger.error("Activate sponsorship is not yet implemented")

        # update sms request
        sms_request.complete_step2()
        self.button_generate_invoices()
        return True
