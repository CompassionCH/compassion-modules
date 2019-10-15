# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json

from odoo import _
from odoo.http import request, route, Response
from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.exceptions import MissingError
from werkzeug.exceptions import NotFound


class PaymentFormController(website_account, FormControllerMixin):

    @route(['/compassion/payment/invoice/<int:invoice_id>'], type='http',
           website=True, methods=['GET', 'POST'],
           auth='public', noindex=['header', 'meta', 'robots'], csrf=False)
    def payment_invoice(self, invoice_id, **kwargs):
        """ Controller for redirecting to the payment submission of an invoice.

        :param invoice_id: account.invoice record created previously.
        """
        try:
            invoice = request.env['account.invoice'].sudo().browse(invoice_id)
        except MissingError:
            invoice = request.env['account.invoice']
        if invoice.state == 'paid':
            return request.render('cms_form_compassion.payment_already_done')
        if not invoice.exists():
            raise NotFound()

        acquirer = request.env['payment.acquirer'].search(
            [('website_published', '=', True),
             ('company_id', '=', invoice.company_id.id)],
            limit=1
        )
        if not acquirer:
            raise Exception('There is no configured acquirer!')

        transaction = self.get_transaction(invoice_id)

        if not transaction or (transaction.state != 'draft' and
                               transaction.state != 'pending'):
            transaction = request.env['payment.transaction'].sudo()
            reference = transaction.get_next_reference(
                invoice.origin or 'WEB')
            transaction = transaction.create({
                'acquirer_id': acquirer.id,
                'type': 'form',
                'amount': invoice.amount_total,
                'currency_id': invoice.currency_id.id,
                'partner_id': invoice.partner_id.id,
                'reference': reference,
                'invoice_id': invoice_id,
                'accept_url': kwargs.get('accept_url', invoice.accept_url),
                'decline_url': kwargs.get('decline_url', invoice.decline_url),
            })
            request.session['compassion_transaction_id'] = transaction.id

        acquirer_button = acquirer.with_context(
            submit_class='btn btn-primary',
            submit_txt=_('Pay Now')
        ).sudo().render(
            transaction.reference,
            transaction.amount,
            transaction.currency_id.id,
            values={
                'return_url': kwargs.get('redirect_url',
                                         '/compassion/payment/validate'),
                'partner_id': transaction.partner_id.id,
                'billing_partner_id': transaction.partner_id.id,
            }
        )
        acquirer.button = acquirer_button
        values = {
            'acquirer': acquirer,
            'invoice': invoice
        }

        template = 'cms_form_compassion.modal_payment_submit' if \
            kwargs.get('display_type') == 'modal' else \
            'cms_form_compassion.payment_submit_full'
        return request.render(template, values)

    @route(['/compassion/payment/<int:transaction_id>'],
           auth="public", website=True, csrf=False)
    def payment(self, transaction_id, **kwargs):
        """ Controller for redirecting to the payment submission, using
        an existing transaction.

        :param int transaction_id: id of a payment.transaction record.
        """
        transaction = self.get_transaction()

        values = {
            'payment_form': transaction.acquirer_id.with_context(
                submit_class='btn btn-primary',
                submit_txt=_('Next')
            ).sudo().render(
                transaction.reference,
                transaction.amount,
                transaction.currency_id.id,
                values={
                    'return_url': kwargs['redirect_url'],
                    'partner_id': transaction.partner_id.id,
                    'billing_partner_id': transaction.partner_id.id,
                }
            ),
            'acquirer_id': transaction.acquirer_id.id,
        }
        template = 'cms_form_compassion.modal_payment_submit' if \
            kwargs['display_type'] == 'modal' else \
            'cms_form_compassion.payment_submit_full'
        return request.render(template, values)

    @route('/compassion/payment/validate',
           type='http', auth='public', website=True,
           noindex=['header', 'meta', 'robots'], csrf=False)
    def payment_validate(self, transaction_id=None, **post):
        payment_ok = True
        if transaction_id is None:
            tx = self.get_transaction()
        else:
            tx = request.env['payment.transaction'].sudo() \
                .browse(transaction_id)

        if not tx.invoice_id or tx.state not in ('done', 'authorized'):
            payment_ok = False

        if payment_ok and tx.accept_url:
            return request.redirect(tx.accept_url)
        if not payment_ok and tx.decline_url:
            return request.redirect(tx.decline_url)

        # If no redirection is set, use the default template
        return request.render(
            'invoice_postfinance_payment_controller.payment_redirect',
            {'payment_ok': payment_ok,
             'tx': tx,
             }
        )

    @route(['/compassion/payment/stripe/create_charge'], type='json',
           auth='public', csrf=False)
    def stripe_create_charge(self, **post):
        """ Create a payment transaction for stripe

        Expects the result from the user input from checkout.js popup"""
        tx = request.env['payment.transaction'].sudo().browse(
            int(request.session.get('compassion_transaction_id') or
                request.session.get('sale_transaction_id') or
                request.session.get('website_payment_tx_id', False))
        )
        response = tx._create_stripe_charge(tokenid=post['tokenid'],
                                            email=post['email'])

        if response:
            request.env['payment.transaction'].sudo().with_context(
                lang=None).form_feedback(response, 'stripe')
        return post.pop('return_url', '/')

    def get_transaction(self, invoice_id=None):
        if invoice_id:
            transaction = request.env['payment.transaction'].sudo() \
                .search(
                [('invoice_id', '=', invoice_id)], limit=1, order='id DESC')
            if transaction:
                return transaction

        tx_id = request.session.get('compassion_transaction_id')
        if tx_id:
            try:
                transaction = request.env['payment.transaction'].sudo() \
                    .browse(tx_id).exists()
                if transaction:
                    return transaction
                else:
                    request.session['compassion_transaction_id'] = False
            except MissingError:
                request.session['compassion_transaction_id'] = False
        return False

    def compassion_payment_validate(
            self, transaction, success_template, fail_template, **kwargs):
        """
        Common payment validate method: checks state of transaction and
        pay related invoice if everything is fine. Redirects to given urls.
        :param transaction: payment.transaction record
        :param success_template: payment success redirect url
        :param fail_template: payment failure redirect url
        :param kwargs: post data
        :return: web page
        """
        if transaction.state == 'done':
            return request.render(success_template, kwargs)
        else:
            return request.render(fail_template, kwargs)

    def _form_redirect(self, response, full_page=False):
        """
        Utility for payment form that are called by AJAX and can send back
        a redirection. Instead of pushing back the redirection which will
        fail over HTTPS, we wrap it inside JSON response and let the client
        perform the redirection.
        :param response: original response
        :param full_page: optional parameter to force full page rendering
                          (useful for modal forms that must close the modal)
        :return: Response object for client
        """
        if response.status_code in (302, 303):
            location = ''
            if response.status_code == 303 and request.env.lang != \
                    request.website.default_lang_code:
                # Prepend with lang, to avoid 302 redirection
                location += '/' + request.env.lang
            location += response.location
            res = Response(
                json.dumps({'redirect': location, 'full_page': full_page}),
                status=200,
                mimetype='application/json'
            )
            return res
        return response
