# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job, related_action
import logging

_logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    group_id = fields.Many2one(required=False)
    sms_request_id = fields.Many2one('sms.child.request', 'SMS request',
                                     compute='_compute_sms_request_id')

    @api.multi
    def _compute_sms_request_id(self):
        for contract in self:
            contract.sms_request_id = self.env['sms.child.request'].search([
                ('sponsorship_id', '=', contract.id)
            ], limit=1)

    @api.model
    @job
    def create_sms_sponsorship(self, vals, partner, sms_child_request):
        """ Creates sponsorship from REACT webapp data.
        :param vals: form values
        :param partner: res.partner record
        :param sms_child_request: sms.child.request record
        :return: True
        """
        frontend_lang = self.env['res.lang'].search([
            ('code', 'like', vals['lang'] + '_')], limit=1)
        if not partner:
            # Search for existing partner
            partner = self.env['res.partner'].search([
                ('firstname', 'ilike', vals['firstname']),
                ('lastname', 'ilike', vals['lastname']),
                ('email', '=', vals['email'])
            ])
            if len(partner) > 1:
                partner = partner.filtered('has_sponsorships')
                if len(partner) != 1:
                    partner = False
        else:
            if not (partner.firstname == vals['firstname'] and
                    partner.lastname == vals['lastname']):
                    partner = False
            partner.email = vals['email']

        if not partner:
            partner = self.env['res.partner'].create({
                'firstname': vals['firstname'],
                'lastname': vals['lastname'],
                'mobile': vals['mobile'],
                'email': vals['email'],
                'lang': frontend_lang.code or sms_child_request.lang_code
            })
            sms_child_request.new_partner = True
            sms_child_request.partner_id = partner

        # Update language of request and of partner
        if frontend_lang and partner.lang != frontend_lang.code:
            partner.lang = frontend_lang.code
        sms_child_request.write({
            'partner_id': partner.id,
            'lang_code': partner.lang
        })

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
        sponsorship._set_next_invoice_date_sms()
        sponsorship.with_delay().put_child_on_no_money_hold()
        partner.set_privacy_statement(origin='new_sponsorship')
        sms_child_request.with_context(lang=partner.lang).complete_step1(
            sponsorship.id)
        return True

    @job(default_channel="root.sms_sponsorship")
    @related_action(action='related_action_contract')
    def finalize_form(self, pay_first_month_ebanking, payment_mode_id):
        """ validate sms sponsorship after step 2 and send confirmation email
        :param pay_first_month_ebanking: has the sponsor paid first month
        :param payment_mode_id: selected payment mode
        :return: True
        """
        self.associate_group(payment_mode_id)
        if self.sms_request_id.new_partner:
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
            self.button_generate_invoices()

        if not pay_first_month_ebanking:
            # update sms request and send confirmation. this will be done
            # after the payment if the sponsor decides to pay the first month
            self.sms_request_id.complete_step2()

        return True

    @job(default_channel="root.sms_sponsorship")
    @related_action(action='related_action_contract')
    def post_message_from_step2(self, message):
        # Post message in sponsorship
        notify_ids = self.env['staff.notification.settings'].get_param(
            'new_partner_notify_ids')
        intro = _(
            "Please verify the following information given by the sponsor:")
        return self.message_post(
            intro + message, _("New SMS sponsorship information"),
            partner_ids=notify_ids,
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html',
        )

    def associate_group(self, payment_mode_id):
        """ Create contract group when SMS sponsorship is validated.
        :param payment_mode_id: selected payment mode
        :return: True
        """
        group = self.env['recurring.contract.group'].search([
            ('partner_id', '=', self.partner_id.id),
            ('payment_mode_id', '=', payment_mode_id)
        ], order='next_invoice_date desc', limit=1)
        if not group:
            group = group.create({
                'partner_id': self.partner_id.id,
                'payment_mode_id': payment_mode_id,
            })
        self.group_id = group
        return True

    @job(default_channel="root.sms_sponsorship")
    @related_action(action='related_action_contract')
    def create_first_sms_invoice(self):
        """In case the sponsor is a new partner, create first invoice
        because the sponsorship won't be validated and invoices are not
        generated. We therefore manually create an invoice that can be paid
        online.
        :return: True
        """
        invoicer = self.env['recurring.invoicer'].create({
            'source': "SMS Sponsorship"})
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', 1)], limit=1)
        inv_data = self.group_id._setup_inv_data(journal, invoicer, self)
        self.env['account.invoice'].create(inv_data)
        self.update_next_invoice_date()
        return True

    def contract_waiting(self):
        """
        In case a new sponsor has already paid the first month, we
        automatically pay the first invoice when contract is validated,
        supposing that the staff has verified the partner.
        :return: True
        """
        super(RecurringContract, self).contract_waiting()
        self._post_payment_first_month()
        return True

    def _post_payment_first_month(self):
        for contract in self.filtered('invoice_line_ids'):
            invoices = contract.invoice_line_ids.mapped('invoice_id')
            payment = self.env['account.payment'].search([
                ('invoice_ids', 'in', invoices.ids),
                ('state', '=', 'draft')
            ])
            draft_invoices = invoices.filtered(lambda i: i.state == 'draft')
            draft_invoices.action_invoice_open()
            payment.post()

    def _set_next_invoice_date_sms(self):
        """ Just compute the default next_invoice_date for new sponsorship. """
        self.ensure_one()
        current_date = datetime.today()
        if self.group_id:
            contract_group = self.group_id
            if contract_group.next_invoice_date:
                next_group_date = fields.Datetime.from_string(
                    contract_group.next_invoice_date)
                next_invoice_date = current_date.replace(
                    day=next_group_date.day)
            else:
                next_invoice_date = current_date.replace(day=1)
        else:
            next_invoice_date = current_date.replace(day=1)

        next_invoice_date += relativedelta(months=+1)
        self.next_invoice_date = fields.Date.to_string(next_invoice_date)
