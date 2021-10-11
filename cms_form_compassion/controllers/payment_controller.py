##############################################################################
#
#    Copyright (C) 2019-2021 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from werkzeug.exceptions import NotFound

from odoo.exceptions import MissingError
from odoo.http import request, route

from odoo.addons.account_payment.controllers.portal import PortalAccount


class PaymentFormController(PortalAccount):

    @route(
        ["/compassion/payment/invoice/<int:invoice_id>"],
        type="http",
        website=True,
        methods=["GET", "POST"],
        auth="public",
        sitemap=False,
    )
    def payment_transaction(self, invoice_id, return_url=None,
                            access_token=None, **kwargs):
        """
        Payment route in order to pay an invoice, without using the default
        template showing the invoice. This is useful for donations or to be called
        from a cms.form where we don't need a recap on what the user will pay for.
        :param invoice_id:      id of the invoice to pay
        :param return_url:     return page after payment. If not provided, it will
                               redirect to the default portal invoice view.
        :param access_token:    access token for authorizing view when public user
        :param kwargs:          All other request parameters
        :return: Renders the page
        """
        try:
            invoice = request.env["account.invoice"].sudo().browse(invoice_id)
        except MissingError:
            invoice = request.env["account.invoice"].sudo()
        if invoice.state == "paid":
            return request.render("cms_form_compassion.payment_already_done")
        if not invoice.exists():
            raise NotFound()

        values = self._invoice_get_page_view_values(invoice, access_token, **kwargs)
        invoice_url = invoice.get_portal_url()
        values.update({
            "invoice": invoice,
            "return_url": return_url or invoice_url,
        })
        return request.render("cms_form_compassion.payment_submit", values)
