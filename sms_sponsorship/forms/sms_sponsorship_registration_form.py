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

from odoo import api, models, fields, tools, _

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

        origin_text = fields.Char('I have heard of Compassion through')

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
            fieldset = [
                {
                    'id': 'partner',
                    'title': _('Your personal data'),
                    'fields': ['partner_title', 'partner_firstname',
                               'partner_lastname', 'partner_lang',
                               'partner_email',
                               'partner_phone', 'partner_street',
                               'partner_zip', 'partner_city',
                               'partner_country_id', 'partner_birthdate']
                },
            ]
            if not self.main_object.sudo().origin_id:
                fieldset.append({
                    'id': 'origin',
                    'title': _('How did you hear about Compassion?'),
                    'fields': [
                        'origin_text'
                    ]
                })
            fieldset.append({
                'id': 'payment',
                'title': _('Payment Method'),
                'fields': [
                    'payment_mode_id', 'gtc_accept', 'amount'
                ]
            })
            return fieldset

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
                [], limit=1)
            return statement.text

        @property
        def form_msg_success_updated(self):
            # override to remove text saying item updated after registration
            return

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
            pay_first_month_ebanking = extra_values.get(
                'pay_first_month_ebanking')
            sponsorship.with_delay(eta=delay).finalize_form(
                pay_first_month_ebanking, values['payment_mode_id'])
            if pay_first_month_ebanking and \
                    sponsorship.sms_request_id.new_partner:
                delay = datetime.now() + relativedelta(seconds=5)
                sponsorship.with_delay(eta=delay).create_first_sms_invoice()
            message_post_values = self._get_post_message_values(extra_values)
            if message_post_values:
                body = u"<ul>{}</ul>".format(u"".join(
                    [u"<li>{}: {}</li>".format(k, v) for k, v in
                     message_post_values.iteritems()]
                ))
                sponsorship.with_delay().post_message_from_step2(body)
            # Store payment setting for redirection
            self.pay_first_month_ebanking = pay_first_month_ebanking

        def form_next_url(self, main_object=None):
            if self.pay_first_month_ebanking:
                return super(PartnerSmsRegistrationForm, self).form_next_url(
                    main_object)
            else:
                return self._payment_accept_redirect

        def _edit_transaction_values(self, tx_values, form_vals):
            """ Add invoice link and change reference. """
            tx_values.update({
                'reference': 'SMS-1MONTH-' + self.main_object.display_name,
                'sponsorship_id': self.main_object.id
            })

        def _get_post_message_values(self, form_vals):
            """
            This is used to get values that will posted on the sponsorship.
            :return: dict of key values
            """
            values = {}
            origin = form_vals.get('origin_text')
            if origin:
                values['Origin'] = origin
            return values

        def _get_partner_keys(self):
            res = super(PartnerSmsRegistrationForm, self)._get_partner_keys()
            res.extend(['lang', 'birthdate'])
            res.remove('state_id')
            return res
