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

        _default_amount = None

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

        @property
        def _default_currency_id(self):
            # Muskathlon payments are in CHF
            return self.env.ref('base.CHF').id

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
            tx_values = {
                'acquirer_id': self.acquirer_id.id,
                'type': 'form',
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'partner_country_id': self.partner_id.sudo().country_id.id,
                'reference': 'payment-form',
            }
            self._edit_transaction_values(tx_values)
            transaction_obj = self.env['payment.transaction'].sudo()
            tx_values['reference'] = transaction_obj.get_next_reference(
                tx_values['reference'])
            transaction = transaction_obj.create(tx_values)
            return '/compassion/payment/{}/?redirect_url={}&display_type={}'\
                .format(str(transaction.id), self._payment_accept_redirect,
                        self._display_type)

        def form_before_create_or_update(self, values, extra_values):
            super(PaymentForm, self).form_before_create_or_update(
                values, extra_values)
            # Extract values from form to fields
            source_vals = extra_values or values
            acquirer_id = source_vals.get('acquirer_id')
            if acquirer_id and not self.acquirer_id:
                self.acquirer_id = acquirer_id
            currency_id = source_vals.get('currency_id',
                                          self.env.ref('base.CHF').id)
            if currency_id and not self.currency_id:
                self.currency_id = int(currency_id)
            amount = source_vals.get('amount')
            if amount and not self.amount:
                self.amount = float(amount)

        def form_after_create_or_update(self, values, extra_values):
            """ Dismiss status message, as the client will be redirected
            to payment."""
            self.o_request.website.get_status_message()

        def _edit_transaction_values(self, tx_values):
            """ Hook to setup custom values for payment. """
            pass
