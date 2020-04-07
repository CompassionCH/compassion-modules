##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, tools

testing = tools.config.get("test_enable")


if not testing:
    # prevent these forms to be registered when running tests

    class PaymentForm(models.AbstractModel):
        """A form that creates an invoice and includes payment after submission."""

        _name = "cms.form.payment"
        _description = "Payment Form"
        _inherit = "cms.form"

        # Can either be "modal" or "full" depending if the payment form is
        # displayed in a modal view or in a full page.
        _display_type = "modal"

        # Internal field for the payment process: it will use the generated invoice
        # for payment. All the display of the form and the logic for invoice creation
        # must be implemented in inherited forms.
        invoice_id = fields.Many2one("account.invoice", "Invoice for payment")

        # Properties for page redirect after payment
        @property
        def _payment_success_redirect(self):
            return ""

        @property
        def _payment_error_redirect(self):
            return ""

        def form_next_url(self, main_object=None):
            # Redirect to payment controller
            return (
                f"/compassion/payment/invoice/{self.invoice_id.id}?success_url="
                f"{self._payment_success_redirect}&error_url="
                f"{self._payment_error_redirect}&display_type={self._display_type}"
            )

        def generate_invoice(self):
            """Inherit this method in order to create the invoice that will
            be used for the web payment."""
            return self.env["account.invoice"]

        def form_after_create_or_update(self, values, extra_values):
            """ Dismiss status message, as the client will be redirected
            to payment."""
            super().form_after_create_or_update(values, extra_values)
            self.invoice_id = self.generate_invoice()
            if self.invoice_id.state == 'draft':
                self.invoice_id.action_invoice_open()
