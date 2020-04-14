##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json

from werkzeug.exceptions import NotFound

from odoo.exceptions import MissingError
from odoo.http import request, route, Response, Controller


class PaymentFormController(Controller):

    @route(
        ["/compassion/payment/invoice/<int:invoice_id>"],
        type="http",
        website=True,
        methods=["GET", "POST"],
        auth="public",
        noindex=["header", "meta", "robots"],
        sitemap=False
    )
    def payment_transaction(self, invoice_id, success_url=None, error_url=None,
                            display_type="full", **kwargs):
        """
        Payment route in order to pay an invoice, without using the default
        template showing the invoice. This is useful for donations or to be called
        from a cms.form where we don't need a recap on what the user will pay for.
        :param invoice_id:      id of the invoice to pay
        :param success_url:     return page for success. If not provided, it will
                                redirect to the default portal invoice view.
        :param error_url:       return page for error. If not provided, it will
                                redirect to the default portal invoice view.
        :param display_type:    full/modal (useful for embedding the view in a modal
                                form)
        :param kwargs:          All other request parameters
        :return: Renders the page
        """
        try:
            invoice = request.env["account.invoice"].sudo().browse(invoice_id)
        except MissingError:
            invoice = request.env["account.invoice"]
        if invoice.state == "paid":
            return request.render("cms_form_compassion.payment_already_done")
        if not invoice.exists():
            raise NotFound()

        acquirers = request.env["payment.acquirer"].search([
            ("website_published", "=", True),
            ("company_id", "=", invoice.company_id.id)
        ])
        invoice_url = invoice.get_portal_url()
        values = {
            "invoice": invoice,
            # Taken from /website_payment/pay route
            "acquirers": [acq for acq in acquirers
                          if acq.payment_flow in ['form', 's2s']],
            "pms": request.env['payment.token'].search([
                ('acquirer_id', 'in', acquirers.filtered(
                    lambda x: x.payment_flow == 's2s').ids)]),
            "success_url": success_url or invoice_url,
            "error_url": error_url or invoice_url,
        }
        template = "payment_submit_full" if display_type == "full" else \
            "modal_payment_submit"
        return request.render(f"cms_form_compassion.{template}", values)

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
            location = ""
            if (
                    response.status_code == 303
                    and request.env.lang != request.website.default_lang_code
            ):
                # Prepend with lang, to avoid 302 redirection
                location += "/" + request.env.lang
            location += response.location
            res = Response(
                json.dumps({"redirect": location, "full_page": full_page}),
                status=200,
                mimetype="application/json",
            )
            return res
        return response
