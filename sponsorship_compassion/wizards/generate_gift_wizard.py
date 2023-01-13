##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import calendar
import logging
import os

from dateutil import parser
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import config
from odoo.addons.recurring_contract.models.product_names import GIFT_PRODUCTS_REF, PRODUCT_GIFT_CHRISTMAS

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
        self.ensure_one()
        if not self.description:
            self.description = self.product_id.display_name
        invoice_ids = []
        for contract in (self.env["recurring.contract"]
                .browse(self.env.context.get("active_ids", list()))
                .filtered(lambda c: "S" in c.type and c.state in ['active', 'waiting'])
        ):
            # Logs an error if the birthdate is missing and skip iteration
            if self.product_id.default_code == GIFT_PRODUCTS_REF[0] and not contract.child_id.birthdate:
                logger.error("The birthdate of the child is missing!")
                continue
            # Sets the invoice date to the one in the context if it exists
            invoice_date = self.invoice_date if self.env.context.get("force_date") else False
            if not invoice_date:
                # Computes the invoice date for birthday gifts
                if self.product_id.default_code == GIFT_PRODUCTS_REF[0]:
                    invoice_date, late = self.compute_date_gift_invoice(
                        contract.child_id.birthdate, self.invoice_date
                    )
                # Computes the invoice date for Christmas gifts
                else:
                    invoice_date, late = self.compute_date_gift_invoice(
                        parser.parse(
                            self.env["ir.config_parameter"].sudo().get_param(
                                "sponsorship_compassion.christmas_inv_due_date",
                                default=fields.Date.today().replace(month=12, day=25)
                            ), fuzzy=True
                        ).date(), self.invoice_date
                    )
            if not self.force:
                date_start = datetime.today().replace(month=1, day=1).date()
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
                        ("state", "!=", "cancel")
                    ]
                )
                if inv_lines:
                    continue

            inv_data = self.with_context({"invoice_contract": contract})._build_invoice_gen_data(invoice_date,
                                                                                                 self.env.context.get(
                                                                                                     "invoicer"))
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

    @api.model
    def compute_date_gift_invoice(self, gift_event_date, invoice_due_date):
        """
        Set date of invoice two months before gift event
        :param gift_event_date: date of the gift evemt
        :param invoice_due_date: due date of the invoice
        :return: new_date, late (new invoice due date, whether the invoice is late or not)
        """
        new_date = invoice_due_date
        gift_event_date = gift_event_date.replace(year=datetime.today().year)
        late = False
        # Calculate the difference in months between the gift event date and invoice due date
        month_diff = (gift_event_date.month - invoice_due_date.month) % 12
        if month_diff >= 2:
            # If the gift event date is more than 2 months after the invoice due date,
            # set the new date two months before the gift event date
            new_date = gift_event_date + relativedelta(months=-2)
        elif month_diff <= 0:
            # If the gift date is passed we generate for next year
            new_date = gift_event_date + relativedelta(months=-2, years=+1)
        else:
            new_date = invoice_due_date
        # Ensure that the day of the new date is within the range of days in the month
        new_date = new_date.replace(day=min(new_date.day, calendar.monthrange(new_date.year, new_date.month)[1]))
        return new_date, late

    def _build_invoice_gen_data(self, invoicing_date, invoicer):
        """ Setup a dict with data passed to invoice.create.
            If any custom data is wanted in invoice from contract group, just
            inherit this method.
        """
        self.ensure_one()
        contract = self.env.context.get("invoice_contract")
        if not contract:
            raise Exception(f"This method should get a contract passt to context.\n{os.path.basename(__file__)}")
        partner_id = contract.partner_id.id
        # Cannot create contract with different multiple (is it possible ?)
        partner_product_price_list = self.env['product.pricelist']._get_partner_pricelist_multi([partner_id],
                                                                                                company_id=contract.company_id)
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', contract.company_id.id)
        ], limit=1)
        inv_data = {
            'payment_reference': contract.group_id.ref,  # Accountant reference
            'ref': contract.group_id.ref,  # Internal reference
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'journal_id': journal.id,
            'currency_id': partner_product_price_list.get(partner_id).currency_id.id,
            'invoice_date': invoicing_date,  # Accountant date
            'date': datetime.now(),  # Date of generation of the invoice
            'recurring_invoicer_id': invoicer.id,
            'payment_mode_id': contract.group_id.payment_mode_id.id,
            'company_id': contract.company_id.id,
            # Field for the invoice_due_date to be automatically calculated
            'invoice_payment_term_id': contract.partner_id.property_payment_term_id.id or self.env.ref(
                "account.account_payment_term_immediate").id,
            'invoice_line_ids': [
                (0, 0, self.build_inv_lines_data(contract))
            ],
            'narration': "\n".join(contract.comment or "")
        }
        return inv_data

    def build_inv_lines_data(self, contract):
        """ Setup a dict with data passed to invoice_line.create.
        If any custom data is wanted in invoice line from contract,
        just inherit this method.
        :return: list of dictionaries
        """
        return {
            'name': self.product_id.name,
            'price_unit': self.amount,
            'quantity': 1,
            'product_id': self.product_id.id,
            'contract_id': contract.id,
            'account_id': self.product_id.with_company(
                contract.company_id.id).property_account_income_id.id or False
        }
