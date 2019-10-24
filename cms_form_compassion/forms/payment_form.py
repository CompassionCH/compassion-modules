# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class PaymentForm(models.AbstractModel):
        """A form that includes payment after submission."""

        _name = 'cms.form.payment'
        _inherit = 'cms.form'

        _payment_accept_redirect = '/website_payment/confirm'
        # Can either be modal or full depending if the payment form is
        # displayed in a modal view or in a full page.
        _display_type = 'modal'

        partner_id = fields.Many2one('res.partner')
        amount = fields.Float(required=True)
        currency_id = fields.Many2one('res.currency', 'Currency')
        acquirer_ids = fields.Many2many(
            'payment.acquirer', string='Payment Method')
        acquirer_id = fields.Many2one('payment.acquirer', 'Selected acquirer')
        # Used for redirection to payment transaction
        transaction_id = 0

        @property
        def _default_currency_id(self):
            # Muskathlon payments are in CHF
            return self.env.ref('base.CHF').id

        @property
        def _default_amount(self):
            return 0

        @property
        def form_widgets(self):
            # Hide fields
            res = super(PaymentForm, self).form_widgets
            res.update({
                'currency_id': 'cms_form_compassion.form.widget.hidden',
                'acquirer_ids': 'cms_form_compassion.form.widget.payment',
            })
            return res

        def _form_load_currency_id(
                self, fname, field, value, **req_values):
            return req_values.get('currency_id', self._default_currency_id)

        def _form_load_amount(
                self, fname, field, value, **req_values):
            return req_values.get('amount', self._default_amount)

        def _form_validate_amount(self, value, **req_values):
            try:
                amount = float(value)
                if amount <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return 'amount', _(
                    'Please control the amount')
            # No error
            return 0, 0

        def form_next_url(self, main_object=None):
            # Redirect to payment controller, creating a transaction
            return '/compassion/payment/{}?redirect_url={}&display_type={}'\
                .format(str(self.transaction_id),
                        self._payment_accept_redirect, self._display_type)

        def form_after_create_or_update(self, values, extra_values):
            """ Dismiss status message, as the client will be redirected
            to payment."""
            super(PaymentForm, self).form_after_create_or_update(
                values, extra_values)
            self.o_request.website.get_status_message()
            all_vals = self.get_all_vals(values, extra_values)
            partner = self.env['res.partner'].sudo().browse(
                all_vals.get('partner_id')).exists()
            tx_values = {
                'acquirer_id': all_vals.get('acquirer_id'),
                'type': 'form',
                'amount': all_vals.get('amount'),
                'currency_id': all_vals.get('currency_id'),
                'partner_id': partner.id,
                'partner_country_id': partner.country_id.id,
                'reference': 'payment-form',
            }
            self._edit_transaction_values(tx_values, all_vals)
            transaction_obj = self.env['payment.transaction'].sudo()
            tx_values['reference'] = transaction_obj.get_next_reference(
                tx_values['reference'])
            self.transaction_id = transaction_obj.create(tx_values).id
            self.request.session['compassion_transaction_id'] = self.transaction_id

        def get_all_vals(self, values, extra_values):
            """
            Used to find form value that can either be in values or
            extra_values dictionary.
            :param values: values dictionary (containing form model fields)
            :param extra_values: extra_values dictionary
                                 (containing non-model fields)
            :return: new dictionary that intersect the two sources
            """
            all_vals = values.copy()
            all_vals.update(extra_values)
            return all_vals

        def _edit_transaction_values(self, tx_values, form_vals):
            """ Hook to setup custom values for payment. """
            pass
