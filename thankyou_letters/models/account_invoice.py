##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from collections import OrderedDict

from odoo import fields, models

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"

    communication_id = fields.Many2one(
        "partner.communication.job",
        "Thank you letter",
        ondelete="set null",
        readonly=True,
        copy=False,
    )
    avoid_thankyou_letter = fields.Boolean(
        help="Check to disable thank you letter for donation",
    )

    def _invoice_paid_hook(self):
        """Generate a Thank you Communication when invoice is a donation
        (no sponsorship product inside)
        """
        super()._invoice_paid_hook()
        invoices = self._filter_invoice_to_thank()
        if invoices:
            invoices.generate_thank_you()

    def _compute_amount(self):
        """When invoice is open again, remove it from donation receipt."""
        payment_states = self.mapped("payment_state")
        super()._compute_amount()
        new_payment_states = self.mapped("payment_state")
        for i, state in enumerate(payment_states):
            invoice = self[i]
            if (
                state == "paid"
                and new_payment_states[i] != "paid"
                and invoice.communication_id.state == "pending"
            ):
                invoice.with_delay().cancel_thankyou_letter()

    def group_by_partner(self):
        """Returns a dict with {partner_id: invoices}"""
        res = dict()
        for partner in self.mapped("partner_id"):
            res[partner.id] = self.filtered(
                lambda i, _partner=partner: i.partner_id == _partner
            )
        return OrderedDict(
            sorted(
                res.items(),
                key=lambda t: sum(t[1].mapped("amount_total")),
                reverse=True,
            )
        )

    def generate_thank_you(self):
        """
        Creates a thankyou letter communication.
        """
        partners = self.mapped("partner_id").filtered(
            lambda p: p.thankyou_preference != "none"
        )
        for partner in partners.mapped("commercial_partner_id"):
            invoice_lines = self.mapped("invoice_line_ids").filtered(
                lambda line, p_partner=partner: line.partner_id == p_partner
            )
            if invoice_lines:
                invoice_lines.with_delay().generate_thank_you()

    def cancel_thankyou_letter(self):
        self.ensure_one()
        comm = self.communication_id
        object_ids = comm.object_ids or ""
        comm.unlink()
        # Check if the communication needs to be refreshed.
        for line in self.invoice_line_ids:
            object_ids = (
                object_ids.replace(str(line.id), "").replace(",,", "").strip(",")
            )
        if object_ids:
            # Refresh donation receipt
            remaining_lines = self.env["account.move.line"].browse(
                [int(i) for i in object_ids.split(",")]
            )
            remaining_lines.generate_thank_you()

    def _filter_invoice_to_thank(self):
        """
        Given a recordset of paid invoices, return only those that have
        to be thanked.
        :return: account.invoice recordset
        """
        return self.filtered(
            lambda i: i.move_type == "out_invoice"
            and not i.avoid_thankyou_letter
            and any(i.line_ids.mapped("product_id.requires_thankyou"))
            and (not i.communication_id or i.communication_id.state == "pending")
        )
