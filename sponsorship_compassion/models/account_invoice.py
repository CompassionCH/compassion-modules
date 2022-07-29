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

    _inherit = "account.invoice"

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
        oldname="invoice_type"
    )

    def _compute_children(self):
        """ View children contained in invoice. """
        for invoice in self:
            children = invoice.mapped("invoice_line_ids.contract_id.child_id")
            if len(children) > 1:
                num_children = len(children)
                invoice.children = f"{num_children} children"
            elif children:
                invoice.children = children.local_id
            else:
                invoice.children = False

    @api.depends("payment_move_line_ids", "state" , "move_id.line_ids.full_reconcile_id")
    def _compute_last_payment(self):
        for invoice in self.filtered("payment_move_line_ids"):
            mv_filter = "credit" if invoice.type == "out_invoice" else "debit"
            payment_dates = invoice.payment_move_line_ids.filtered(mv_filter).mapped(
                "date"
            )
            invoice.last_payment = max(payment_dates or [False])

    @api.depends("invoice_line_ids", "state", "invoice_line_ids.product_id")
    def _compute_invoice_category(self):
        sponsorship_cat = self.env.ref(
            "sponsorship_compassion.product_category_sponsorship", False
        )
        fund_cat = self.env.ref("sponsorship_compassion.product_category_fund", False)
        gift_cat = self.env.ref("sponsorship_compassion.product_category_gift", False)
        # At module installation, the categories are not yet loaded.
        if not sponsorship_cat or not fund_cat or not gift_cat:
            return
        for invoice in self.filtered(lambda i: i.state in ("open", "paid")):
            # check if child_of Sponsorship category
            category_lines = self.env["account.invoice.line"].search(
                [
                    ("invoice_id", "=", invoice.id),
                    ("product_id.categ_id", "=", sponsorship_cat.id),
                ]
            )

            if category_lines:
                invoice.invoice_category = "sponsorship"
            else:
                # check if child_of Gift category
                category_lines = self.env["account.invoice.line"].search(
                    [
                        ("invoice_id", "=", invoice.id),
                        ("product_id.categ_id", "=", gift_cat.id),
                    ]
                )
                if category_lines:
                    invoice.invoice_category = "gift"
                else:
                    # check if child_of Fund category
                    category_lines = self.env["account.invoice.line"].search(
                        [
                            ("invoice_id", "=", invoice.id),
                            ("product_id.categ_id", "=", fund_cat.id),
                        ]
                    )
                    if category_lines:
                        invoice.invoice_category = "fund"
                    else:
                        # last choice -> Other category
                        invoice.invoice_category = "other"

    def recompute_category(self):
        self._compute_invoice_category()
