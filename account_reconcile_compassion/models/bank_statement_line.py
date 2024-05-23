##############################################################################
#
#    Copyright (C) 2014-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from functools import reduce

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import mod10r

from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_CATEGORY,
    SPONSORSHIP_CATEGORY,
)

logger = logging.getLogger(__name__)


class BankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    _order = "statement_id asc,is_reconciled desc,partner_id asc,id asc"

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_statement_line_for_reconciliation_widget(self):
        # Add partner reference for reconcile view
        res = super().get_statement_line_for_reconciliation_widget()
        res["partner_ref"] = self.partner_id.ref
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def process_reconciliation(
        self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None
    ):
        """Create invoice if product_id is set in move_lines
        to be created."""
        self.ensure_one()
        partner_invoices = dict()
        partner_inv_data = dict()
        old_counterparts = dict()
        if counterpart_aml_dicts is None:
            counterpart_aml_dicts = list()
        if new_aml_dicts is None:
            new_aml_dicts = list()
        partner_id = self.partner_id.id
        counterparts = [data["move_line"] for data in counterpart_aml_dicts]
        counterparts = reduce(
            lambda m1, m2: m1 + m2.filtered("move_id"),
            counterparts,
            self.env["account.move.line"],
        )
        index = 0
        for mv_line_dict in new_aml_dicts:
            # Add partner_id if missing from mvl_data
            mv_line_dict["partner_id"] = partner_id
            if mv_line_dict.get("product_id"):
                # Create invoice
                if partner_id in partner_inv_data:
                    partner_inv_data[partner_id].append(mv_line_dict)
                else:
                    partner_inv_data[partner_id] = [mv_line_dict]
                mv_line_dict["index"] = index

            index += 1
            if counterparts:
                # An invoice exists for that partner, we will use it
                # to put leftover amount in it, if any exists.
                invoice = counterparts[0].move_id
                partner_invoices[partner_id] = invoice
                old_counterparts[invoice.id] = counterparts[0]

        # Create invoice and update move_line_dicts to reconcile them.
        nb_new_aml_removed = 0
        for partner_id, partner_data in list(partner_inv_data.items()):
            invoice = partner_invoices.get(partner_id)
            new_counterpart = self._create_invoice_from_mv_lines(partner_data, invoice)
            if invoice:
                # Remove new move lines
                for data in partner_data:
                    index = data.pop("index") - nb_new_aml_removed
                    del new_aml_dicts[index]
                    nb_new_aml_removed += 1

                # Update old counterpart
                for counterpart_data in counterpart_aml_dicts:
                    if counterpart_data["move_line"] == old_counterparts[invoice.id]:
                        counterpart_data["move_line"] = new_counterpart
                        counterpart_data["credit"] = new_counterpart.debit
                        counterpart_data["debit"] = new_counterpart.credit
            else:
                # Add new counterpart and remove new move line
                for data in partner_data:
                    index = data.pop("index") - nb_new_aml_removed
                    del new_aml_dicts[index]
                    nb_new_aml_removed += 1
                    data["move_line"] = new_counterpart
                    counterpart_aml_dicts.append(data)

        # Consume invalid fields for move creation
        for mv_line_dict in counterpart_aml_dicts:
            mv_line_dict.pop("avoid_thankyou_letter", False)
            mv_line_dict.pop("sponsorship_id", False)
        for mv_line_dict in new_aml_dicts:
            mv_line_dict.pop("avoid_thankyou_letter", False)
            mv_line_dict.pop("sponsorship_id", False)
        return super().process_reconciliation(
            counterpart_aml_dicts, payment_aml_rec, new_aml_dicts
        )

    def _create_invoice_from_mv_lines(self, mv_line_dicts, invoice=None):
        # Generate a unique bvr_reference
        if self.ref:
            ref = self.ref
        else:
            ref = mod10r(
                str(self.date).replace("-", "")
                + str(self.statement_id.id)
                + str(self.id)
            ).ljust(26, "0")

        if invoice:
            invoice.button_draft()
            invoice.write(
                {
                    "invoice_origin": self.statement_id.name,
                    "invoice_line_ids": [
                        (0, 0, self._get_invoice_line_data(vals))
                        for vals in mv_line_dicts
                    ],
                }
            )

        else:
            # Lookup for an existing open invoice matching the criterias
            invoices = self._find_open_invoice(mv_line_dicts)
            if invoices:
                # Get the bvr reference of the invoice or set it
                invoice = invoices[0]
                invoice.write({"invoice_origin": self.statement_id.name})
                if invoice.payment_reference and not self.ref:
                    ref = invoice.payment_reference
                else:
                    invoice.write({"ref": ref})
                self.write({"ref": ref})
                raise UserError(_("Invoice already exists with ref: ") + ref)

            # Setup a new invoice if no existing invoice is found
            invoice = self.env["account.move"].create(
                self._get_invoice_data(ref, mv_line_dicts)
            )

        invoice.action_post()
        self.ref = ref

        # Update move_lines data
        counterpart = invoice.line_ids.filtered(lambda ml: ml.debit > 0)
        return counterpart

    def _get_invoice_data(self, ref, mv_line_dicts):
        """
        Sets the invoice
        :param ref: reference of the statement line
        :param mv_line_dicts: all data for reconciliation
        :return: dict of account.move vals
        """
        journal_id = (
            self.env["account.journal"]
            .search(
                [("type", "=", "sale"), ("company_id", "=", self.company_id.id)],
                limit=1,
            )
            .id
        )

        avoid_thankyou = any(
            map(lambda mvl: mvl.pop("avoid_thankyou_letter"), mv_line_dicts)
        )
        comment = ";".join([d.pop("comment", "") for d in mv_line_dicts])

        return {
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "journal_id": journal_id,
            "invoice_date": self.date,
            "ref": ref,
            "narration": comment,
            # When a foreign currency is set the reconciliation is made on that currency
            "currency_id": self.foreign_currency_id.id or self.currency_id.id,
            "payment_mode_id": self.statement_id.journal_id.payment_mode_id.id,
            "avoid_thankyou_letter": avoid_thankyou,
            "invoice_line_ids": [
                (0, 0, self._get_invoice_line_data(mld)) for mld in mv_line_dicts
            ],
            "bank_statement_id": self.statement_id.id,
        }

    def _get_invoice_line_data(self, mv_line_dict):
        """
        Setup invoice line data
        :param mv_line_dict: values from the move_line reconciliation
        :return: dict of account.invoice.line vals
        """
        amount = mv_line_dict["credit"]
        account_id = mv_line_dict["account_id"]
        invl_vals = {
            "name": self.name,
            "account_id": account_id,
            "price_unit": amount,
            "price_subtotal": amount,
            # "user_id": mv_line_dict.get("user_id"),
            "quantity": 1,
            "product_id": mv_line_dict["product_id"],
            "analytic_account_id": mv_line_dict["analytic_account_id"],
            "analytic_tag_ids": mv_line_dict["analytic_tag_ids"],
        }
        # Remove analytic account from bank journal item:
        # it is only useful in the invoice journal item
        analytic = mv_line_dict.pop("analytic_account_id", False)
        if analytic:
            invl_vals["analytic_account_id"] = analytic

        # Find sponsorship
        sponsorship_id = mv_line_dict.pop("sponsorship_id")
        contract = self.env["recurring.contract"].browse(sponsorship_id)
        invl_vals["contract_id"] = contract.id

        # Force sponsorship when GIFT invoice is selected
        product = self.env["product.product"].browse(mv_line_dict["product_id"])
        if product.categ_name in (GIFT_CATEGORY, SPONSORSHIP_CATEGORY) and not contract:
            raise UserError(_("Add a Sponsorship"))

        # Find analytic default if possible
        default_analytic = self.env["account.analytic.default"].account_get(
            product.id, self.partner_id.id
        )
        analytic = invl_vals.get("analytic_account_id")
        if not analytic and default_analytic:
            invl_vals["analytic_account_id"] = default_analytic.analytic_id.id

        return invl_vals

    def _find_open_invoice(self, mv_line_dicts):
        """Find an open invoice that matches the statement line and which
        could be reconciled with."""
        invoice_line_obj = self.env["account.move.line"]
        inv_lines = invoice_line_obj
        for mv_line_dict in mv_line_dicts:
            amount = mv_line_dict["credit"]
            inv_lines |= invoice_line_obj.search(
                [
                    ("partner_id", "child_of", mv_line_dict.get("partner_id")),
                    ("move_id.state", "=", "posted"),
                    ("move_id.payment_state", "=", "not_paid"),
                    ("product_id", "=", mv_line_dict.get("product_id")),
                    ("price_subtotal", "=", amount),
                ]
            )

        return inv_lines.mapped("move_id").filtered(
            lambda i: i.amount_total == self.amount
        )
