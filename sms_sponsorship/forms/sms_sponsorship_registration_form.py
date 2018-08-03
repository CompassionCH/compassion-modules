# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import re

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')
_logger = logging.getLogger(__name__)

if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _name = 'cms.form.recurring.contract'
        _inherit = 'cms.form'

        _form_model = 'recurring.contract'
        _form_model_fields = ['partner_id', 'payment_mode_id']
        _form_required_fields = ('partner_id', 'payment_mode_id')

        partner_title = fields.Many2one(
            'res.partner.title', 'Title', required=True)
        partner_name = fields.Char('Name', required=True)
        partner_email = fields.Char('Email', required=True)
        partner_phone = fields.Char('Phone', required=True)
        partner_street = fields.Char('Street', required=True)
        partner_zip = fields.Char('Zip', required=True)
        partner_city = fields.Char('City', required=True)
        partner_country_id = fields.Many2one(
            'res.country', 'Country', required=True)
        pay_first_month_ebanking = fields.Boolean("Pay first month with "
                                                  "e-banking ?")
        immediately_add_gifts = fields.Boolean("Directly send gifts to the "
                                               "child ?")

        @property
        def form_title(self):
            return _("Confirm your sponsorship for %s ") %\
                   self.main_object.sudo().child_id.preferred_name

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'partner',
                    'description': _('Your personal data'),
                    'fields': ['partner_title', 'partner_name',
                               'partner_email',
                               'partner_phone', 'partner_street',
                               'partner_zip', 'partner_city',
                               'partner_country_id']
                },
                {
                    'id': 'payment',
                    'description': _('Your payment mode'),
                    'fields': [
                        'payment_mode_id'
                    ]
                },
                {
                    'id': 'optional',
                    'description': _('Optional choices'),
                    'fields': [
                        'pay_first_month_ebanking',
                        'immediately_add_gifts'
                    ]
                }
            ]

        def form_init(self, request, main_object=None, **kw):
            form = super(PartnerSmsRegistrationForm, self).form_init(
                request, main_object, **kw)

            # Set default values in the model
            partner = main_object.sudo().partner_id
            form.partner_id = partner.id
            form.partner_title = partner.title
            form.partner_name = partner.name
            form.partner_email = partner.email
            form.partner_phone = partner.phone
            form.partner_street = partner.street
            form.partner_zip = partner.zip
            form.partner_city = partner.city
            form.partner_country_id = partner.country_id or \
                self.env.ref('base.ch')
            form.pay_first_month_ebanking = False
            form.immediately_add_gifts = False
            return form

        # Load values from model into form view
        #######################################
        def _form_load_partner_id(self, fname, field, value, **req_values):
            return req_values.get('partner_id', self.partner_id or '')

        def _form_load_partner_name(self, fname, field, value, **req_values):
            return req_values.get('partner_name', self.partner_name or '')

        def _form_load_partner_title(self, fname, field, value, **req_values):
            return req_values.get('partner_title', self.partner_title.id or '')

        def _form_load_partner_email(self, fname, field, value, **req_values):
            return req_values.get('partner_email', self.partner_email or '')

        def _form_load_partner_phone(self, fname, field, value, **req_values):
            return req_values.get('partner_phone', self.partner_phone or '')

        def _form_load_partner_street(self, fname, field, value, **req_values):
            return req_values.get('partner_street', self.partner_street or '')

        def _form_load_partner_zip(self, fname, field, value, **req_values):
            return req_values.get('partner_zip', self.partner_zip or '')

        def _form_load_partner_city(self, fname, field, value, **req_values):
            return req_values.get('partner_city', self.partner_city or '')

        def _form_load_partner_country_id(
                self, fname, field, value, **req_values):
            # Default value loaded in website form
            return int(req_values.get('partner_country_id',
                                      self.partner_country_id.id))

        # Form validation
        #################
        def _form_validate_partner_phone(self, value, **req_values):
            if not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'phone', _('Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_partner_zip(self, value, **req_values):
            if not re.match(r'^\d{3,6}$', value):
                return 'zip', _('Please enter a valid zip code')
            # No error
            return 0, 0

        def _form_validate_partner_email(self, value, **req_values):
            if not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')
            # No error
            return 0, 0

        def _form_validate_partner_name(self, value, **req_values):
            return self._form_validate_alpha_field('name', value)

        def _form_validate_partner_street(self, value, **req_values):
            return self._form_validate_alpha_field('street', value)

        def _form_validate_partner_city(self, value, **req_values):
            return self._form_validate_alpha_field('city', value)

        def _form_validate_alpha_field(self, field, value):
            if not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

        # Form submission
        #################
        def form_before_create_or_update(self, values, extra_values):
            super(PartnerSmsRegistrationForm,
                  self).form_before_create_or_update(values, extra_values)

            sponsorship = self.main_object.sudo()
            partner = sponsorship.partner_id
            partner_vals = self._get_partner_vals(extra_values)
            if partner:
                # update existing partner
                partner.write(partner_vals)
            else:
                # create new partner
                self.env['res.partner'].sudo().create(partner_vals)

            # creates group_id and payment_id if first sponsorship of
            # partner
            if not sponsorship.payment_mode_id:
                sponsorship.group_id = self.env[
                    'recurring.contract.group'].sudo().create({
                        'partner_id': partner.id,
                        'payment_mode_id': values['payment_mode_id']
                    })

        def form_after_create_or_update(self, values, extra_values):
            # validate sponsorship and send confirmation email
            sponsorship = self.main_object.sudo()
            sms_request = self.env['sms.child.request'].sudo().search([
                ('sponsorship_id', '=', self.main_object.id)
            ])
            # check if partner was created via the SMS request. new_partner
            # is set at True in recurring_contract in models
            if sms_request.new_partner:
                # send staff notification
                notify_ids = self.env['staff.notification.settings'].get_param(
                    'new_partner_notify_ids')
                if notify_ids:
                    sponsorship.message_post(
                        body=_("A new partner was created by SMS and needs a "
                               "manual confirmation"),
                        subject=_("New SMS partner"),
                        partner_ids=notify_ids,
                        type='comment',
                        subtype='mail.mt_comment',
                        content_subtype='plaintext'
                    )
            else:
                sponsorship.signal_workflow('contract_validated')

            # if sponsor directly payed
            if self.pay_first_month_ebanking:
                # load payment view ? TODO
                _logger.error("Activate sponsorship is not yet implemented")

            # update sms request
            sms_request.complete_step2()
            sponsorship.button_generate_invoices()

        def form_next_url(self, main_object=None):
            return "/sms_sponsorship/step2/" + str(self.main_object.id) + \
                   "/confirm"

        # override to remove text saying item updated after registration
        @property
        def form_msg_success_updated(self):
            return

        def _get_partner_vals(self, values):
            return {
                key.replace('partner_', ''): value
                for key, value in values.iteritems()
                if key.startswith('partner_')
            }
