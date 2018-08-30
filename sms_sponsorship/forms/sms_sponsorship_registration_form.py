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
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')
_logger = logging.getLogger(__name__)

if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _name = 'cms.form.recurring.contract'
        _inherit = ['cms.form.match.partner', 'cms.form.payment']

        _form_model = 'recurring.contract'
        _form_model_fields = ['partner_id', 'payment_mode_id']
        _form_required_fields = ('partner_id', 'payment_mode_id', 'gtc_accept')
        _display_type = 'full'

        # These two fields are not used for now but we let them in case
        # we would like to revert the functionality
        pay_first_month_ebanking = fields.Boolean("Pay first month now")
        immediately_add_gifts = fields.Boolean("Directly send gifts to the "
                                               "child ?")
        gtc_accept = fields.Boolean(
            "Terms and conditions", required=True
        )

        @property
        def _payment_accept_redirect(self):
            return "/sms_sponsorship/step2/" + str(self.main_object.id) + \
                "/confirm"

        @property
        def form_title(self):
            return _("Confirm your sponsorship for %s ") %\
                self.main_object.sudo().child_id.preferred_name

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'partner',
                    'title': _('Your personal data'),
                    'fields': ['partner_title', 'partner_name',
                               'partner_email',
                               'partner_phone', 'partner_street',
                               'partner_zip', 'partner_city',
                               'partner_country_id']
                },
                {
                    'id': 'payment',
                    'fields': [
                        'payment_mode_id', 'gtc_accept', 'amount'
                    ]
                },
            ]

        @property
        def form_widgets(self):
            # Hide fields
            res = super(PartnerSmsRegistrationForm, self).form_widgets
            res.update({
                'amount': 'cms_form_compassion.form.widget.hidden',
                'acquirer_ids':
                'cms_form_compassion.form.widget.payment.hidden',
                'gtc_accept': 'cms_form_compassion.form.widget.terms',
            })
            return res

        @property
        def _default_amount(self):
            return self.main_object.total_amount

        @property
        def gtc(self):
            statement = self.env['compassion.privacy.statement'].sudo().search(
                [], limit=1).with_context(lang=self.partner_id.sudo().lang)
            return statement.text

        @property
        def form_msg_success_updated(self):
            # override to remove text saying item updated after registration
            return

        def form_init(self, request, main_object=None, **kw):
            form = super(PartnerSmsRegistrationForm, self).form_init(
                request, main_object, **kw)

            # Set default values in the model
            sms_request = form.main_object.sudo().sms_request_id
            partner = main_object.sudo().partner_id
            form.partner_id = partner.id
            form.partner_title = partner.title
            form.partner_name = partner.name
            form.partner_email = partner.email
            form.partner_phone = sms_request.sender or partner.mobile or \
                partner.phone
            form.partner_street = partner.street
            form.partner_zip = partner.zip
            form.partner_city = partner.city
            form.partner_country_id = partner.country_id or \
                self.env.ref('base.ch')
            form.pay_first_month_ebanking = kw.get('pay_first_month_ebanking')
            form.immediately_add_gifts = kw.get('immediately_add_gifts')
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

        # Form submission
        #################
        def form_before_create_or_update(self, values, extra_values):
            super(PartnerSmsRegistrationForm,
                  self).form_before_create_or_update(values, extra_values)

            sponsorship = self.main_object.sudo()
            partner = sponsorship.partner_id
            partner_vals = self._get_partner_vals(values, extra_values)
            if partner:
                # update existing partner (later, to avoid rollbacks)
                delay = datetime.now() + relativedelta(minutes=1)
                partner.with_delay(eta=delay).update_partner(partner_vals)
            else:
                # create new partner
                self.env['res.partner'].sudo().create(partner_vals)

        def _form_write(self, values):
            """ Nothing to do on write, we handle everything in other methods.
            """
            return True

        def form_after_create_or_update(self, values, extra_values):
            delay = datetime.now() + relativedelta(seconds=3)
            sponsorship = self.main_object.sudo()
            sponsorship.with_delay(eta=delay).finalize_form(
                self.pay_first_month_ebanking, values['payment_mode_id'])
            if self.pay_first_month_ebanking and \
                    sponsorship.sms_request_id.new_partner:
                delay = datetime.now() + relativedelta(seconds=5)
                sponsorship.with_delay(eta=delay).create_first_sms_invoice()

        def form_next_url(self, main_object=None):
            if self.pay_first_month_ebanking:
                return super(PartnerSmsRegistrationForm, self).form_next_url(
                    main_object)
            else:
                return self._payment_accept_redirect

        def _edit_transaction_values(self, tx_values):
            """ Add invoice link and change reference. """
            tx_values.update({
                'reference': 'SMS-1MONTH-' + self.main_object.display_name,
                'sponsorship_id': self.main_object.id
            })
