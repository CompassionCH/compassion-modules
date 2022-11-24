##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

from odoo import api, fields, models


class AccountInvoice(models.Model):
    """Generate automatically a BVR Reference for LSV Invoices"""

    _inherit = "account.move"

    children = fields.Char("Children", compute="_compute_children")
    last_payment = fields.Date(compute="_compute_last_payment", store=True)
    invoice_category = fields.Selection(
        [
            ("sponsorship", "Sponsorship"),
            ("gift", "Gift"),
            ("fund", "Fund donation"),
            ("other", "Other"),
        ],
        compute="_compute_invoice_category",
        store=True,
    )

    def _compute_children(self):
        """ View children contained in invoice. """
        for invoice in self:
            children = invoice.mapped("line_ids.contract_id.child_id")
            if len(children) > 1:
                num_children = len(children)
                invoice.children = f"{num_children} children"
            elif children:
                invoice.children = children.local_id
            else:
                invoice.children = False

    @api.depends("payment_state")
    def _compute_last_payment(self):
        for invoice in self:
            if invoice.line_ids.full_reconcile_id:
                mv_filter = "credit" if invoice.move_type == "out_invoice" else "debit"
                payment_dates = invoice.line_ids.filtered(mv_filter).mapped(
                    "date"
                )
                invoice.last_payment = max(payment_dates or [False])
            else:
                invoice.last_payment = False

    @api.depends("line_ids", "payment_state", "line_ids.product_id")
    def _compute_invoice_category(self):
        categ_obj = self.env["product.category"]
        sponsorship_cat = self.env.ref(
            "sponsorship_compassion.product_category_sponsorship", categ_obj
        )
        fund_cat = self.env.ref("sponsorship_compassion.product_category_fund", categ_obj)
        gift_cat = self.env.ref("sponsorship_compassion.product_category_gift", categ_obj)
        for invoice in self:
            categories = invoice.invoice_line_ids.mapped("product_id.categ_id")
            if sponsorship_cat and sponsorship_cat in categories:
                invoice.invoice_category = "sponsorship"
            elif gift_cat and gift_cat in categories:
                invoice.invoice_category = "gift"
            elif fund_cat and fund_cat in categories:
                invoice.invoice_category = "fund"
            else:
                # last choice -> Other category
                invoice.invoice_category = "other"

    def recompute_category(self):
        self._compute_invoice_category()

    def update_invoices(self, updt_val):
        """ Method that update given invoices in self with the value of updt_val
            :param updt_val dict    is a dictionnary of invoices value with the invoice name
            { 'SLE/289482' : { 'amount': XXX }}
        """
        for invoice in self:
            invoice.button_draft()
            val_to_modify = updt_val.get(invoice.name)
            # Simplify for the caller by transforming amount into a account.move.line
            final_val = dict()
            if "amount" in val_to_modify:
                amt = val_to_modify.get("amount")
                if amt == 0:
                    invoice._cancel_invoice()
                    continue
                else:
                    final_val["invoice_line_ids"] = invoice._build_invoice_line(val_to_modify.get("amount"))
            invoice.write(final_val)
            invoice.action_post()

    def _build_invoice_line(self, amt):
        self.ensure_one()
        return [(1, self.invoice_line_ids.id, {"price_unit": amt})]

    def _cancel_invoice(self):
        self.ensure_one()
        self.button_cancel()
