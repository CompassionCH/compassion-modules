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

from odoo import _, fields, models

from ..models.product_names import GIFT_PRODUCTS_REF

_logger = logging.getLogger(__name__)


class GenerateGiftWizard(models.TransientModel):
    """This wizard generates a Gift Invoice for a given contract."""

    _name = "generate.gift.wizard"
    _description = "Gift Generation Wizard"

    amount = fields.Float("Gift Amount", required=True)
    product_id = fields.Many2one(
        "product.product", "Gift Type", required=True, readonly=False
    )
    contract_ids = fields.Many2many(
        "recurring.contract",
        string="Contracts",
        default=lambda self: self.env.context.get("active_ids"),
        readonly=False,
    )
    contract_id = fields.Many2one(
        "recurring.contract", help="Current contract for invoice generation"
    )
    invoice_date = fields.Date(default=fields.Date.today)
    description = fields.Char("Additional comments", size=200)
    quantity = fields.Integer(default=1)
    bypass_invoice_suspension = fields.Boolean(default=False)

    def generate_invoice(self, due_date=None):
        if not self.description:
            self.description = self.product_id.display_name
        invoice_ids = []
        # Retrieve contracts eligible for gift generation
        contracts = self.contract_ids.filtered(
            lambda c: "S" in c.type
            and c.state in ["active", "waiting"]
            and c.is_gift_authorized
        )
        invoicer = self.env.context.get("invoicer", self.env["recurring.invoicer"])
        invoice_obj = self.env["account.move"]
        for contract in contracts:
            # Logs an error if the birthdate is missing and skip iteration
            if (
                self.product_id.default_code == GIFT_PRODUCTS_REF[0]
                and not contract.child_id.birthdate
            ):
                _logger.error("The birthdate of the child is missing!")
                continue

            self.contract_id = contract
            # Sets the invoice date to the one in the context if it exists
            invoice_date = (
                self.invoice_date if self.env.context.get("force_date") else due_date
            )

            # if the generation is suspended we don't want the gift to be generated
            if (
                contract.group_id.invoice_suspended_until
                and contract.group_id.invoice_suspended_until > invoice_date
                and not self.bypass_invoice_suspension
            ):
                _logger.warning("The invoices are suspended")
                continue
            inv_data = contract.group_id._build_invoice_gen_data(
                invoicing_date=invoice_date,
                invoicer=invoicer,
                gift_wizard=self,
            )
            # This makes sure all move lines have the correct contract
            invoice = invoice_obj.with_context(default_contract_id=contract.id).create(
                inv_data
            )
            invoice.partner_bank_id = contract.partner_id.bank_ids[:1].id
            invoice.action_post()
            invoice_ids.append(invoice.id)
        return {
            "name": _("Generated Invoices"),
            "view_mode": "list,form",
            "res_model": "account.move",
            "domain": [("id", "in", invoice_ids)],
            "type": "ir.actions.act_window",
        }
