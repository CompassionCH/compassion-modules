##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import config
from ..models.product_names import GIFT_PRODUCTS_REF, PRODUCT_GIFT_CHRISTMAS

logger = logging.getLogger(__name__)
test_mode = config.get("test_enable")


class GenerateGiftWizard(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """

    _name = "generate.gift.wizard"
    _description = "Gift Generation Wizard"

    amount = fields.Float("Gift Amount", required=True)
    product_id = fields.Many2one(
        "product.product", "Gift Type", required=True, readonly=False
    )
    invoice_date = fields.Date(default=fields.Date.today())
    description = fields.Char("Additional comments", size=200)
    force = fields.Boolean(
        "Force creation",
        help="Creates the gift even if one was already " "made the same year.",
    )

    def generate_invoice(self):
        # Read data in english
        self.ensure_one()
        if not self.description:
            self.description = self.product_id.display_name
        invoice_ids = list()
        gen_states = self.env["recurring.contract.group"]._get_gen_states()

        # Ids of contracts are stored in context
        for contract in (
                self.env["recurring.contract"]
                        .browse(self.env.context.get("active_ids", list()))
                        .filtered(lambda c: "S" in c.type and c.state in gen_states)
        ):
            if self.product_id.default_code in (GIFT_PRODUCTS_REF[0], PRODUCT_GIFT_CHRISTMAS):
                if self.env.context.get("force_date"):
                    invoice_date = self.invoice_date
                else:
                    invoice_date = False

                if self.product_id.default_code == GIFT_PRODUCTS_REF[0]:
                    # Birthday Gift
                    if not contract.child_id.birthdate:
                        logger.error("The birthdate of the child is missing!")
                        continue
                    # This is set in the view in order to let the user
                    # choose the invoice date. Otherwise (called from code)
                    # the invoice date will be computed based on the
                    # birthday of the child.
                    if not invoice_date:
                        invoice_date, late = self.compute_date_gift_invoice(
                            contract.child_id.birthdate, self.invoice_date
                        )
                else:
                    if not invoice_date:
                        invoice_date, late = self.compute_date_gift_invoice(
                            datetime.strptime(self.env["ir.config_parameter"].sudo().get_param(
                                "sponsorship_compassion.christmas_inv_due_date"),
                                '%Y-%m-%d'
                            ).date(), self.invoice_date
                        )
            else:
                invoice_date = self.invoice_date
            inv_data = self._setup_invoice(contract, invoice_date)
            invoice = self.env["account.move"].create(inv_data)
            invoice.partner_bank_id = contract.partner_id.bank_ids[:1].id
            invoice.action_post()
            # Commit at each invoice creation. This does not break
            # the state
            if not test_mode:
                self.env.cr.commit()  # pylint: disable=invalid-commit
            invoice_ids.append(invoice.id)

        return {
            "name": _("Generated Invoices"),
            "view_mode": "list,form",
            "res_model": "account.move",
            "domain": [("id", "in", invoice_ids)],
            # "context": {"form_view_ref": "sponsorship_compassion.view_invoice_child_form"},
            "type": "ir.actions.act_window",
        }

    def _setup_invoice(self, contract, invoice_date):
        journal_id = (
            self.env["account.journal"]
            .search(
                [("type", "=", "sale"), ("company_id", "=", contract.company_id.id)],
                limit=1,
            )
            .id
        )
        return {
            "move_type": "out_invoice",
            "partner_id": contract.gift_partner_id.id,
            "journal_id": journal_id,
            'currency_id': contract.company_id.currency_id.id,
            "invoice_date": invoice_date,
            "payment_mode_id": contract.payment_mode_id.id,
            "company_id": contract.mapped('company_id')[:1].id,
            "recurring_invoicer_id": self.env.context.get(
                "recurring_invoicer_id", False
            ),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    self.with_context(journal_id=journal_id)._setup_invoice_line(
                        contract
                    ),
                ),
            ],
        }

    def _setup_invoice_line(self, contract):
        self.ensure_one()
        product = self.product_id

        inv_line_data = {
            "name": self.description,
            "account_id": product.with_company(contract.company_id.id).property_account_income_id.id or False,
            "price_unit": self.amount,
            "quantity": 1,
            "product_id": product.id,
            "contract_id": contract.id,
        }

        # Define analytic journal
        analytic = self.env["account.analytic.default"].account_get(
            product.id, contract.partner_id.id, date=fields.Date.today()
        )
        if analytic.analytic_id:
            inv_line_data["analytic_account_id"] = analytic.analytic_id.id
        if analytic.analytic_tag_ids:
            inv_line_data["analytic_tag_ids"] = [(6, 0, analytic.analytic_tag_ids.ids)]

        return inv_line_data

    @api.model
    def compute_date_gift_invoice(self, gift_event_date, invoice_due_date):
        """Set date of invoice two months before child's birthdate"""
        new_date = invoice_due_date
        late = False
        if gift_event_date.month >= invoice_due_date.month + 2:
            new_date = invoice_due_date.replace(day=28, month=gift_event_date.month - 2)
        elif gift_event_date.month + 3 < invoice_due_date.month:
            new_date = gift_event_date.replace(
                day=28, year=invoice_due_date.year + 1
            ) + relativedelta(months=-2)
            new_date = max(new_date, invoice_due_date)
            late = True
        return new_date, late
