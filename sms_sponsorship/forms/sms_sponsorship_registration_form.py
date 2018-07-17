# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, api, _

testing = tools.config.get('test_enable')


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _name = 'cms.form.recurring.contract'
        _inherit = 'cms.form.match.partner'

        _form_model = 'recurring.contract'
        _form_model_fields = ('partner_id', 'group_id')
        _form_required_fields = ('partner_id', 'group_id')
        _form_fields_order = ('partner_id', 'group_id')

        payment_mode_id = fields.Many2one(
            default=lambda self: self._get_op_payment_mode())
        pay_first_month_ebanking = fields.Boolean("Pay first month with "
                                                  "e-banking ?")
        immediately_add_gifts = fields.Boolean("Directly send gifts to the "
                                               "child ?")

        @api.model
        def _get_op_payment_mode(self):
            """ Get Permanent Order Payment Term, to set it by default. """
            record = self.env.ref(
                'sponsorship_switzerland.payment_mode_permanent_order')
            return record.id

        def _form_validate_payement_method(self, value, **req_values):
            payment_mode = self.env['account.payment.mode'].with_context(
                lang='en_US').search([
                ('payment_mode_id', '=', self.payment_mode_id.id)
            ])
            payment_name = payment_mode.name
            if 'LSV' not in payment_name or 'Postfinance' not in payment_name:
                return 'payement_method', _('Please enter a valid payement '
                                            'method (LSV or permanent order')
            # No error
            return 0, 0

        def form_init(self, request, main_object=None, **kw):
            form = super(PartnerSmsRegistrationForm, self).form_init(
                request, main_object, **kw)

            # Set default values
            partner_id = self.partner_id

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

        def form_before_create_or_update(self, values, extra_values):
            super(PartnerSmsRegistrationForm, self).form_before_create_or_update(
                values, extra_values)

            partner_id = values.get('partner_id')
            correspondent_id = partner_id.correspondent_id.id

            # form is already filled
            if partner_id and correspondent_id:
                if not self.partner_id:
                    self.partner_id = partner_id
                if not self.correspondent_id:
                    self.correspondent_id = correspondent_id

            return True

        def form_after_create_or_update(self, values, extra_values):
            # activate sponsorship and send welcome-active + confirmation email
            pass
