##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class PaymentForm(models.AbstractModel):
    """A form that creates an invoice and includes payment after submission."""

    _name = "cms.form.payment"
    _description = "Payment Form"
    _inherit = "cms.form"

    # Internal field for the payment process: it will use the generated invoice
    # for payment. All the display of the form and the logic for invoice creation
    # must be implemented in inherited forms.
    invoice_id = fields.Many2one("account.invoice", "Invoice for payment")

    # Properties for page redirect after payment
    @property
    def _payment_redirect(self):
        return ""

    @property
    def form_msg_success_updated(self):
        # override to remove text saying item updated.
        return

    @property
    def form_msg_success_created(self):
        # override to remove text saying item created.
        return

    def form_next_url(self, main_object=None):
        # Redirect to payment controller
        return (
            f"/compassion/payment/invoice/{self.invoice_id.id}?return_url="
            f"{self._payment_redirect}"
        )

    def generate_invoice(self):
        """Inherit this method in order to create the invoice that will
        be used for the web payment."""
        return self.env["account.move"]

    def form_after_create_or_update(self, values, extra_values):
        """ Dismiss status message, as the client will be redirected
        to payment."""
        super().form_after_create_or_update(values, extra_values)
        invoice = self.generate_invoice().sudo()
        self.invoice_id = invoice
        if invoice.state == 'draft':
            for line in invoice.invoice_line_ids.sudo():
                line_vals = line.read(['price_unit', 'quantity', 'price_subtotal'])[0]
                line._onchange_product_id()
                line.write(line_vals)
            if "skip_invoice_validation" not in extra_values:
                invoice.action_post()
