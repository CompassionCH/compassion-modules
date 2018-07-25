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

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')
_logger = logging.getLogger(__name__)


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _name = 'cms.form.recurring.contract'
        _inherit = 'cms.form.match.partner'

        _form_model = 'recurring.contract'
        _form_model_fields = ['partner_id', 'payment_mode_id']
        _form_required_fields = ('partner_id', 'payment_mode_id')

        pay_first_month_ebanking = fields.Boolean("Pay first month with "
                                                  "e-banking ?")
        immediately_add_gifts = fields.Boolean("Directly send gifts to the "
                                               "child ?")

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'partner',
                    'description': _('Your personal data'),
                    'fields': ['partner_title', 'partner_name',
                               'partner_email',
                               'partner_phone', 'partner_street',
                               'partner_zip', 'partner_city']
                },
                {
                    'id': 'payment',
                    'description': _('Your way of payment'),
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

            # Set default values
            partner_id = main_object.partner_id

            if partner_id:
                form.partner_id = partner_id.id
                form.partner_title = partner_id.title
                form.partner_name = partner_id.name
                form.partner_email = partner_id.email
                form.partner_phone = partner_id.phone
                form.partner_street = partner_id.street
                form.partner_zip = partner_id.zip
                form.partner_city = partner_id.city
                form.partner_country_id = partner_id.country_id
                form.partner_state_id = partner_id.state_id

            form.pay_first_month_ebanking = False
            form.immediately_add_gifts = False

            return form

        def _form_load_partner_id(
                self, fname, field, value, **req_values):
            return req_values.get('partner_id', self.partner_id or '')

        def _form_load_partner_name(
                self, fname, field, value, **req_values):
            return req_values.get('partner_name', self.partner_name or '')

        def _form_load_partner_title(
                self, fname, field, value, **req_values):
            return req_values.get('partner_title', self.partner_title.id or '')

        def _form_load_partner_email(
                self, fname, field, value, **req_values):
            return req_values.get('partner_email', self.partner_email or '')

        def _form_load_partner_phone(
                self, fname, field, value, **req_values):
            return req_values.get('partner_phone', self.partner_phone or '')

        def _form_load_partner_street(
                self, fname, field, value, **req_values):
            return req_values.get('partner_street', self.partner_street or '')

        def _form_load_partner_zip(
                self, fname, field, value, **req_values):
            return req_values.get('partner_zip', self.partner_zip or '')

        def _form_load_partner_city(
                self, fname, field, value, **req_values):
            return req_values.get('partner_city', self.partner_city or '')

        def form_before_create_or_update(self, values, extra_values):
            super(PartnerSmsRegistrationForm,
                  self).form_before_create_or_update(values, extra_values)

            partner = self.env['res.partner'].search([
                ('id', '=', self.main_object.partner_id.id)
            ])

            if partner:
                # update existing partner
                partner.write(extra_values)
            else:
                # create new partner
                self.env['res.partner'].create(extra_values)

        def form_after_create_or_update(self, values, extra_values):
            # validate sponsorship and send confirmation email
            self.main_object.signal_workflow('contract_validated')

            # if sponsor directly payed
            if self.pay_first_month_ebanking:
                # load payment view ? TODO
                _logger.error("Activate sponsorship is not yet implemented")

            # update sms request
            self.env['sms.child.request'].sudo()\
                .search([('sponsorship_id', '=', self.main_object.id)])\
                .write({'state': 'step2'})

            # send confirmation mail
            self._send_confirmation_mail()

        def _send_confirmation_mail(self):
            # TODO implement
            pass

        def get_partner_id_from_partner_values(self, values):
            return self.env['res.partner'].search([
                ('name', '=', values.get('partner_name')),
                ('email', '=', values.get('partner_email'))
            ], limit=1).id
