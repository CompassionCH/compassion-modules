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


class PaymentFormController(website_account, FormControllerMixin):

    @route(['/compassion/payment/<int:transaction_id>'],
           auth="public", website=True)
    def payment(self, transaction_id, **kwargs):
        """ Controller for redirecting to the payment submission, using
        an existing transaction.

        :param int transaction_id: id of a payment.transaction record.
        """
        transaction = request.env['payment.transaction'].sudo().browse(
            transaction_id)
        values = {
            'payment_form': transaction.acquirer_id.with_context(
                submit_class='btn btn-primary',
                submit_txt=_('Next')).sudo().render(
                transaction.reference,
                transaction.amount,
                transaction.currency_id.id,
                values={
                    'return_url': kwargs['redirect_url'],
                    'partner_id': transaction.partner_id.id,
                    'billing_partner_id': transaction.partner_id.id,
                }
            )
        }
        template = 'cms_form_compassion.modal_payment_submit' if \
            kwargs['display_type'] == 'modal' else \
            'cms_form_compassion.payment_submit_full'
        return request.render(template, values)

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
