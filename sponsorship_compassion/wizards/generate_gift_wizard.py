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
import os

from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.tools import config
from odoo.addons.recurring_contract.models.product_names import GIFT_PRODUCTS_REF, PRODUCT_GIFT_CHRISTMAS

logger = logging.getLogger(__name__)
test_mode = config.get("test_enable")


class GenerateGiftWizard(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """

    _name = "generate.gift.wizard"
    _description = "Gift Generation Wizard"

    amount = fields.Float("Gift Amount", required=True)
    product_id = fields.Many2one("product.product", "Gift Type", required=True, readonly=False)
    contract_id = fields.Many2one("recurring.contract", "Contract", required=True)
    invoice_date = fields.Date(default=fields.Date.today)
    description = fields.Char("Additional comments", size=200)
    force = fields.Boolean("Force creation", help="Creates the gift even if one was already made the same year.")
    quantity = fields.Integer(default=1)

    def generate_invoice(self):
        self.ensure_one()
        if not self.description:
            self.description = self.product_id.display_name
        invoice_ids = []
        contract = self.contract_id.filtered(lambda c: "S" in c.type and c.state in ['active', 'waiting'])
        if contract:
            # Logs an error if the birthdate is missing and skip iteration
            if self.product_id.default_code == GIFT_PRODUCTS_REF[0] and not contract.child_id.birthdate:
                logger.error("The birthdate of the child is missing!")
                return 1
            # Sets the invoice date to the one in the context if it exists
            invoice_date = self.invoice_date if self.env.context.get("force_date") else False
            if not invoice_date:
                # Computes the invoice date for birthday gifts
                if self.product_id.default_code == GIFT_PRODUCTS_REF[0]:
                    invoice_date = self.compute_date_gift_invoice(
                        contract.child_id.birthdate, self.invoice_date
                    )
                # Computes the invoice date for Christmas gifts
                else:
                    invoice_date = self.compute_date_gift_invoice(
                        date(date.today().year, 12, 25),
                        date(
                            date.today().year,
                            self.env["res.config.settings"].get_param("christmas_inv_due_month", 10),
                            1)
                    )
            if not self.force:
                date_start = date.today().replace(month=1, day=1)
                inv_lines = self.env["account.move.line"].search(
                    [
                        "|",
                        ("due_date", "=", invoice_date),
                        "&",
                        ("move_id.date", ">=", date_start),
                        ("move_id.date", "<=", date_start.replace(month=12)),
                        "&", "&",
                        ("product_id", "=", self.product_id.id),
                        ("contract_id", "=", contract.id),
                        ("parent_state", "!=", "cancel")
                    ]
                )
                if inv_lines:
                    return 1

            inv_data = self._build_invoice_gen_data(invoice_date, self.env.context.get("invoicer"))
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
            "type": "ir.actions.act_window",
        }

    @staticmethod
    def compute_date_gift_invoice(gift_event_date, invoice_due_date):
        """
        Set date of invoice two months before gift event
        :param gift_event_date: date of the gift event
        :param invoice_due_date: due date of the invoice
        :return: new_date, late (new invoice due date, whether the invoice is late or not)
        """
        new_date = gift_event_date.replace(year=date.today().year) + relativedelta(months=-2)
        if new_date < invoice_due_date:
            new_date = new_date + relativedelta(years=1)
        # Ensure that the day of the new date is within the range of days in the month
        new_date = new_date.replace(day=1)
        return new_date

    def _build_invoice_gen_data(self, invoicing_date, invoicer):
        """ Setup a dict with data passed to invoice.create.
            If any custom data is wanted in invoice from contract group, just
            inherit this method.
        """
        if not self.contract_id:
            raise Exception(f"This method should get a contract passt to context.\n{os.path.basename(__file__)}")
        return self.contract_id.group_id._build_invoice_gen_data(invoicing_date=invoicing_date,
                                                                 invoicer=invoicer,
                                                                 gift_wizard=self)
