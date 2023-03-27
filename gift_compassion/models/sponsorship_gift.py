##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import date, timedelta

from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_PRODUCTS_REF,
    GIFT_CATEGORY
)

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SponsorshipGift(models.Model):
    _name = "sponsorship.gift"
    _inherit = ["translatable.model", "mail.thread", "compassion.mapped.model"]
    _description = "Sponsorship Gift"
    _order = "gift_date desc,id desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # Related records
    #################
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Sponsorship", readonly=False
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        related="sponsorship_id.correspondent_id",
        store=True,
        readonly=False,
    )
    project_id = fields.Many2one(
        "compassion.project",
        "Project",
        related="sponsorship_id.project_id",
        store=True,
        readonly=False,
    )
    project_suspended = fields.Boolean(
        related="project_id.hold_gifts", tracking=True
    )
    child_id = fields.Many2one(
        "compassion.child",
        "Child",
        related="sponsorship_id.child_id",
        store=True,
        readonly=False,
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", "gift_id", string="Invoice lines", readonly=True
    )
    payment_id = fields.Many2one(
        "account.move", "GMC Payment", copy=False, readonly=False
    )
    inverse_payment_id = fields.Many2one(
        "account.move", "Inverse move", copy=False, readonly=False
    )
    message_id = fields.Many2one(
        "gmc.message", "GMC message", copy=False, readonly=False
    )

    # Gift information
    ##################
    name = fields.Char(compute="_compute_name", translate=False)
    gmc_gift_id = fields.Char(readonly=True, copy=False)
    gift_date = fields.Date(
        compute="_compute_invoice_fields", inverse=lambda g: True, store=True
    )
    date_partner_paid = fields.Date(
        compute="_compute_invoice_fields", inverse=lambda g: True, store=True
    )
    date_sent = fields.Datetime(
        related="message_id.process_date", store=True, readonly=True
    )
    amount = fields.Float(
        compute="_compute_invoice_fields",
        inverse=lambda g: True,
        store=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_currency",
        readonly=False,
    )
    currency_usd = fields.Many2one(
        "res.currency", compute="_compute_usd", readonly=False
    )
    exchange_rate = fields.Float(readonly=True, copy=False, digits=(12, 6))
    amount_us_dollars = fields.Float("Amount due", readonly=True, copy=False)
    instructions = fields.Char()
    gift_type = fields.Selection(
        "get_gift_type_selection", required=True, string="Gift for"
    )
    attribution = fields.Selection("get_gift_attributions", required=True)
    sponsorship_gift_type = fields.Selection(
        "get_sponsorship_gifts", string="Gift type"
    )
    state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("verify", _("Verify")),
            ("open", _("Pending")),
            ("suspended", _("Suspended")),
            ("In Progress", _("In Progress")),
            ("Delivered", _("Delivered")),
            ("Undeliverable", _("Undeliverable")),
        ],
        default="draft",
        readonly=True,
        tracking=True,
    )
    undeliverable_reason = fields.Selection(
        [
            ("Project Transitioned", "Project Transitioned"),
            ("Beneficiary Exited", "Beneficiary Exited"),
            (
                "Beneficiary Exited/Whereabouts Unknown",
                "Beneficiary Exited/Whereabouts Unknown",
            ),
            (
                "Beneficiary Exited More Than 90 Days Ago",
                "Beneficiary Exited More Than 90 Days Ago",
            ),
        ],
        readonly=True,
        copy=False,
    )
    threshold_alert = fields.Boolean(
        help="Partner exceeded the maximum gift amount allowed",
        readonly=True,
        copy=False,
    )
    threshold_alert_type = fields.Char(readonly=True, copy=False)
    field_office_notes = fields.Char(readonly=True, copy=False)
    status_change_date = fields.Datetime(readonly=True)
    account_credit = fields.Char(compute="_compute_params", readonly=True)
    account_debit = fields.Char(compute="_compute_params", readonly=True)
    journal_id = fields.Char(compute="_compute_params", readonly=True)
    analytic = fields.Char(compute="_compute_params", readonly=True)
    analytic_tag = fields.Char(compute="_compute_params", readonly=True)
    is_param_set = fields.Boolean(compute="_compute_is_param_set", readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def get_gift_type_selection(self):
        return [
            ("Project Gift", _("Project")),
            ("Family Gift", _("Family")),
            ("Beneficiary Gift", _("Beneficiary")),
        ]

    @api.model
    def get_gift_attributions(self):
        return [
            ("Center Based Programming", "CDSP"),
            ("Home Based Programming (Survival & Early Childhood)", "CSP"),
            ("Sponsored Child Family", _("Sponsored Child Family")),
            ("Sponsorship", _("Sponsorship")),
            ("Survival", _("Survival")),
            ("Survival Neediest Families", _("Neediest Families")),
            ("Survival Neediest Families - Split", _("Neediest Families Split")),
        ]

    @api.model
    def get_sponsorship_gifts(self):
        return [
            ("Birthday", _("Birthday")),
            ("General", _("General")),
            ("Graduation/Final", _("Graduation/Final")),
        ]

    @api.depends(
        "invoice_line_ids", "invoice_line_ids.parent_state", "invoice_line_ids.price_subtotal"
    )
    def _compute_invoice_fields(self):
        for gift in self.filtered("invoice_line_ids"):
            invoice_lines = gift.invoice_line_ids
            pay_dates = invoice_lines.filtered("last_payment").mapped(
                "last_payment"
            ) or [False]
            gift.date_partner_paid = fields.Date.to_string(max([d for d in pay_dates]))
            gift.gift_date = max(invoice_lines.mapped('move_id').mapped("invoice_date") or [False])

            gift.amount = sum(invoice_lines.mapped("price_subtotal"))

    def _compute_currency(self):
        # Set gift currency depending on its invoice currency
        self.currency_id = self.sudo().mapped("invoice_line_ids.move_id.currency_id")[:1]

    def _compute_name(self):
        for gift in self:
            if gift.gift_type != "Beneficiary Gift":
                name = gift.translate("gift_type")
            else:
                name = gift.translate("sponsorship_gift_type") + " " + _("Gift")

            if gift.sponsorship_id:
                name += " [" + gift.sponsorship_id.name + "]"
            elif gift.partner_id:
                name += " [" + gift.partner_id.name + "]"
            elif gift.child_id:
                name += " [" + gift.child_id.name + "]"
            elif gift.project_id:
                name += " [" + gift.project_id.name + "]"
            gift.name = name

    def _compute_usd(self):
        for gift in self:
            gift.currency_usd = self.env.ref("base.USD")

    def _compute_is_param_set(self):
        self.is_param_set = all([int(self.account_credit), int(self.account_debit), int(self.journal_id)])

    def _compute_params(self):
        company = self.sponsorship_id.company_id
        param_obj = self.env["res.config.settings"].sudo().with_company(company)
        self.account_credit = param_obj.get_param("gift_income_account_id")
        self.account_debit = param_obj.get_param("gift_expense_account_id")
        self.journal_id = param_obj.get_param("gift_journal_id")
        self.analytic = param_obj.get_param("gift_analytic_id")
        self.analytic_tag = param_obj.get_param("gift_analytic_tag_id")
    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Try to find existing gifts before creating a new one. """
        previous_gift = self._search_for_similar_pending_gifts(vals)
        if previous_gift:
            return previous_gift._blend_in_other_gift(vals)

        # If a gift for the same partner is to verify, put as well
        # the new one to verify.
        partner_id = (
            self.env["recurring.contract"].browse(vals["sponsorship_id"]).partner_id.id
        )
        gift_to_verify = self.search_count(
            [("partner_id", "=", partner_id), ("state", "=", "verify")]
        )
        if gift_to_verify:
            vals["state"] = "verify"
        new_gift = super(SponsorshipGift, self).create(vals)
        if new_gift.invoice_line_ids:
            new_gift.invoice_line_ids.write({"gift_id": new_gift.id})
        else:
            # Prevent computed fields to reset their values
            vals.pop("message_follower_ids")
            new_gift.write(vals)
        new_gift._create_gift_message()
        return new_gift

    def _search_for_similar_pending_gifts(self, vals):
        gift_date = vals.get("gift_date")
        if not gift_date:
            invl = self.env["account.move.line"]
            dates = []
            default = fields.Date.today()
            for invl_write in vals.get("invoice_line_ids", [[3]]):
                if invl_write[0] == 0:
                    dates.append(invl_write[2].get("due_date", default))
                elif invl_write[0] == 4:
                    dates.append(invl.browse(invl_write[1]).due_date)
                elif invl_write[0] == 6:
                    dates.extend(invl.browse(invl_write[2]).mapped("due_date"))
                else:
                    dates.append(default)
            gift_date = max(dates)

        return self.search(
            [
                ("sponsorship_id", "=", vals["sponsorship_id"]),
                ("gift_type", "=", vals["gift_type"]),
                ("attribution", "=", vals["attribution"]),
                ("gift_date", "like", str(gift_date)[:4]),
                ("sponsorship_gift_type", "=", vals.get("sponsorship_gift_type")),
                ("state", "in", ["draft", "verify", "error"]),
            ],
            limit=1,
        )

    def _blend_in_other_gift(self, other_gift_vals):
        self.ensure_one()
        # Update gift invoice lines
        invl_write = list()
        for line_write in other_gift_vals.get("invoice_line_ids", []):
            if line_write[0] == 6:
                # Avoid replacing all line_ids => change (6, 0, ids) to
                # [(4, id), (4, id), ...]
                invl_write.extend([(4, id) for id in line_write[2]])
            else:
                invl_write.append(line_write)
        if invl_write:
            self.write({"invoice_line_ids": invl_write})

        else:
            aggregated_amounts = self.amount + other_gift_vals["amount"]
            self.write({"amount": aggregated_amounts})
        instructions = [self.instructions, other_gift_vals["instructions"]]
        self.instructions = "; ".join([x for x in instructions if x])
        return self

    def unlink(self):
        # Cancel gmc messages
        self.mapped("message_id").unlink()
        to_remove = self.filtered(lambda g: g.state != "Undeliverable")
        for gift in to_remove:
            if gift.gmc_gift_id:
                raise UserError(
                    _("You cannot delete the %s." "It is already sent to GMC.")
                    % gift.name
                )
        return super(SponsorshipGift, to_remove).unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)
        if "id" in odoo_data:
            odoo_data["id"] = int(odoo_data["id"])
        return odoo_data

    def data_to_json(self, mapping_name=None):
        json_data = super().data_to_json(mapping_name)
        if json_data.get("RecipientType") == "Project Gift":
            del json_data["Beneficiary_GlobalID"]
            if json_data.get("RecipientID"):
                json_data["RecipientId"] = json_data["RecipientID"][:6]
                del json_data["RecipientID"]
            else:
                json_data["RecipientId"] = self.project_id.fcp_id
        return json_data

    @api.model
    def create_from_invoice_line(self, invoice_line):
        """
        Creates a sponsorship.gift record from an invoice_line
        :param invoice_line: account.invoice.line record
        :return: sponsorship.gift record
        """

        gift_vals = self.get_gift_values_from_product(invoice_line)
        if not gift_vals:
            return False

        gift = self.create(gift_vals)
        eligible, message = gift.is_eligible()
        if not eligible:
            gift.state = "verify"
            gift.message_post(body=message)
            gift.message_id.state = "postponed"
        return gift

    @api.model
    def get_gift_values_from_product(self, invoice_line):
        """
        Converts a product into sponsorship.gift values
        :param: invoice_line: account.invoice.line record
        :return: dictionary of sponsorship.gift values
        """
        product = invoice_line.product_id
        sponsorship = invoice_line.contract_id
        if not product.categ_name == GIFT_CATEGORY:
            return False

        gift_vals = self.get_gift_types(product)
        if gift_vals:
            gift_vals.update(
                {
                    "sponsorship_id": sponsorship.id,
                    "invoice_line_ids": [(4, invoice_line.id)],
                    "instructions": invoice_line.move_id.narration,
                }
            )

        return gift_vals

    def is_eligible(self):
        """ Verifies the amount is within the thresholds and that the fcp
        is currently accepting gifts.
        """
        self.ensure_one()
        sponsorship = self.sponsorship_id
        if sponsorship.project_id.hold_gifts:
            return False, "Sponsorship may have a project with hold gifts"

        threshold_rule = self.env["gift.threshold.settings"].search(
            [
                ("gift_type", "=", self.gift_type),
                ("gift_attribution", "=", self.attribution),
                ("sponsorship_gift_type", "=", self.sponsorship_gift_type),
            ],
            limit=1,
        )
        if threshold_rule:
            current_rate = threshold_rule.currency_id.rate or 1.0
            minimum_amount = threshold_rule.min_amount
            maximum_amount = threshold_rule.max_amount

            this_amount = self.amount * current_rate
            if this_amount < minimum_amount:
                return False, f"""Gift amount is small than minimal amount, Gift amount: {round(this_amount,2)}$, 
                Minimal amount :{round(minimum_amount,2)}$. """
            if this_amount > maximum_amount:
                return False, f"""Gift amount is higher than maximum amount, Gift amount: {round(this_amount,2)}$, 
                Maximum amount :{round(maximum_amount,2)}$. """

            if threshold_rule.yearly_threshold:
                # search other gifts for the same sponsorship.
                # we will compare the date with the first january of the
                # current year
                next_year = fields.Date.to_string(
                    (date.today() + timedelta(days=365)).replace(month=1, day=1)
                )
                firstJanuaryOfThisYear = fields.Date.today().replace(day=1, month=1)

                other_gifts = self.search(
                    [
                        ("sponsorship_id", "=", sponsorship.id),
                        ("gift_type", "=", self.gift_type),
                        ("attribution", "=", self.attribution),
                        ("sponsorship_gift_type", "=", self.sponsorship_gift_type),
                        ("gift_date", ">=", firstJanuaryOfThisYear),
                        ("gift_date", "<", next_year),
                    ]
                )

                total_amount = this_amount
                if other_gifts:
                    total_amount += sum(
                        other_gifts.mapped(
                            lambda gift: gift.amount_us_dollars
                                         or gift.amount * current_rate
                        )
                    )

                if total_amount > (maximum_amount * threshold_rule.gift_frequency):
                    return False, f"""Yearly threshold exceed: total_amount: {round(total_amount)}$, Yearly threshold: 
                                        {round(maximum_amount,2)}*{round(threshold_rule.gift_frequency,2)} 
                                        = {round(maximum_amount * threshold_rule.gift_frequency,2)}$ """

        return True, ""

    @api.model
    def get_gift_types(self, product):
        """ Given a product, returns the correct values
        of a gift for GMC.

        :return: dictionary of sponsorship.gift values
        """
        gift_type_vals = dict()
        if product.default_code == GIFT_PRODUCTS_REF[0]:
            gift_type_vals.update(
                {
                    "gift_type": "Beneficiary Gift",
                    "attribution": "Sponsorship",
                    "sponsorship_gift_type": "Birthday",
                }
            )
        elif product.default_code == GIFT_PRODUCTS_REF[1]:
            gift_type_vals.update(
                {
                    "gift_type": "Beneficiary Gift",
                    "attribution": "Sponsorship",
                    "sponsorship_gift_type": "General",
                }
            )
        elif product.default_code == GIFT_PRODUCTS_REF[2]:
            gift_type_vals.update(
                {"gift_type": "Family Gift", "attribution": "Sponsored Child Family", }
            )
        elif product.default_code == GIFT_PRODUCTS_REF[3]:
            gift_type_vals.update(
                {
                    "gift_type": "Project Gift",
                    "attribution": "Center Based Programming",
                }
            )
        elif product.default_code == GIFT_PRODUCTS_REF[4]:
            gift_type_vals.update(
                {
                    "gift_type": "Beneficiary Gift",
                    "attribution": "Sponsorship",
                    "sponsorship_gift_type": "Graduation/Final",
                }
            )

        return gift_type_vals

    def on_send_to_connect(self):
        self.write({"state": "open"})

    def on_gift_sent(self, data):
        """
        Called when gifts message is received by GMC.
        Create a move record in the GMC Gift Due Account.
        :return:
        """
        self.ensure_one()
        try:
            exchange_rate = float(data.get("exchange_rate"))
        except ValueError:
            exchange_rate = self.env.ref("base.USD").rate or 1.0
        data.update(
            {"state": "In Progress", "amount_us_dollars": exchange_rate * self.amount}
        )
        account_credit = self.account_credit
        account_debit = self.account_debit
        journal_id = self.journal_id
        # We create the move only if the parameter are set
        if self.is_param_set:
            maturity = (self.date_sent and self.date_sent.date()) or fields.Date.today()
            move_data = {
                "journal_id": journal_id,
                "ref": "Gift payment to GMC",
                "date": maturity,
            }
            move_lines_data = list()
            analytic = self.analytic
            analytic_tag = self.analytic_tag
            product_id = self.sudo().invoice_line_ids[0].product_id.id
            # Create the debit lines from the Gift Account
            invoiced_amount = sum(self.sudo().invoice_line_ids.mapped("price_subtotal") or [0])
            if invoiced_amount:
                for invl in self.sudo().invoice_line_ids:
                    move_lines_data.append(
                        {
                            "partner_id": invl.partner_id.id,
                            "product_id": product_id,
                            "account_id": account_debit,
                            "name": invl.name,
                            "debit": invl.price_subtotal,
                            "credit": 0.0,
                            "analytic_account_id": analytic,
                            "date": maturity,
                            "date_maturity": maturity,
                            "currency_id": self.currency_usd.id,
                            "amount_currency": invl.price_subtotal * exchange_rate,
                            "analytic_tag_ids": [(4, analytic_tag)] if analytic_tag else False
                        }
                    )
            if invoiced_amount < self.amount:
                # Create a move line for the difference that is not invoiced.
                amount = self.amount - invoiced_amount
                move_lines_data.append(
                    {
                        "partner_id": self.partner_id.id,
                        "product_id": product_id,
                        "account_id": account_debit,
                        "name": self.name,
                        "debit": amount,
                        "analytic_account_id": analytic,
                        "date": maturity,
                        "date_maturity": maturity,
                        "currency_id": self.currency_usd.id,
                        "amount_currency": amount * exchange_rate,
                        "analytic_tag_ids": [(4, analytic_tag)] if analytic_tag else False
                    }
                )

            # Create the credit line in the GMC Gift Due Account
            move_lines_data.append(
                {
                    "partner_id": self.partner_id.id,
                    "product_id": product_id,
                    "account_id": account_credit,
                    "name": self.name,
                    "date": maturity,
                    "date_maturity": maturity,
                    "credit": self.amount,
                    "currency_id": self.currency_usd.id,
                    "amount_currency": self.amount * exchange_rate * -1,
                }
            )
            move_data["line_ids"] = [(0, False, line_data) for line_data in move_lines_data]
            move = self.env["account.move"].sudo().create(move_data)
            move.action_post()
            data["payment_id"] = move.id
        else:
            _logger.warning("Please setup income, expense and analytic accounts for gifts if you want to track payments to GMC.")
        self.write(data)

    @api.model
    def process_commkit(self, commkit_data):
        """"
        This function is automatically executed when an Update Gift
        Message is received. It will convert the message from json to odoo
        format and then update the concerned records

        :param commkit_data contains the data of the message (json)
        :return list of gift ids which are concerned by the message
        """
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        gifts_data = commkit_data["GiftUpdatesRequest"]["GiftUpdateRequestList"]
        gift_ids = []
        changed_gifts = self

        # For each dictionary, we update the corresponding record
        for gift_data in gifts_data:
            vals = self.json_to_data(gift_data, "CreateGift")
            gift_id = vals["id"]
            gift_ids.append(gift_id)
            gift = self.env["sponsorship.gift"].browse([gift_id]).exists()
            if vals.get("state", gift.state) != gift.state:
                changed_gifts += gift
            gift.write(vals)

        changed_gifts.filtered(lambda g: g.state == "Delivered")._gift_delivered()
        changed_gifts.filtered(
            lambda g: g.state == "Undeliverable"
        )._gift_undeliverable()

        return gift_ids

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def view_invoices(self):
        return {
            "name": _("Invoices"),
            "domain": [("id", "in", self.invoice_line_ids.mapped("move_id").ids)],
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "target": "current",
        }

    def action_ok(self):
        self.write({"state": "draft"})
        self.mapped("message_id").write({"state": "new"})
        return True

    def action_send(self):
        self.mapped("message_id").process_messages()
        return True

    def action_verify(self):
        self.write({"state": "verify"})
        self.mapped("message_id").write({"state": "postponed"})
        return True

    def action_in_progress(self):
        self.write({"state": "In Progress"})
        self.mapped("payment_id").post()
        return True

    def action_suspended(self):
        self.write({"state": "suspended"})
        self.mapped("payment_id").button_cancel()
        return True

    def action_cancel(self):
        """ Cancel Invoices and delete Gifts. """
        self.mapped("invoice_line_ids.move_id").button_draft()
        self.mapped("message_id").unlink()
        return self.unlink()

    @api.onchange("gift_type")
    def onchange_gift_type(self):
        if self.gift_type == "Beneficiary Gift":
            self.attribution = "Sponsorship"
        elif self.gift_type == "Family Gift":
            self.attribution = "Sponsored Child Family"
            self.sponsorship_gift_type = False
        elif self.gift_type == "Project Gift":
            self.attribution = "Center Based Programming"
            self.sponsorship_gift_type = False

    def mark_sent(self):
        self.mapped("message_id").unlink()
        return self.write(
            {"state": "Delivered", "status_change_date": fields.Datetime.now(), }
        )

    @api.model
    def process_gifts_cron(self):
        gifts = self.search(
            [("state", "=", "draft"), ("gift_date", "<=", fields.Date.today())]
        )
        gifts.mapped("message_id").process_messages()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _create_gift_message(self):
        for gift in self:
            message_obj = self.env["gmc.message"]

            action_id = self.env.ref("gift_compassion.create_gift")

            message_vals = {
                "action_id": action_id.id,
                "object_id": gift.id,
                "partner_id": gift.partner_id.id,
                "child_id": gift.child_id.id,
                "state": "new" if gift.state != "verify" else "postponed",
            }
            gift.message_id = message_obj.create(message_vals)

    def _gift_delivered(self):
        """
        Called when gifts delivered notification is received from GMC.
        """
        pass

    def _gift_undeliverable(self):
        """
        Create an inverse move
        Notify users defined in settings.
        """
        param_obj = self.env["res.config.settings"]
        inverse_credit_account = param_obj.get_param("gift_expense_account_id")
        inverse_debit_account = param_obj.get_param("gift_income_account_id")
        analytic = param_obj.get_param("gift_analytic_id")
        analytic_tag = param_obj.get_param("gift_analytic_tag_id")
        for gift in self.filtered("payment_id"):
            pay_move = gift.payment_id
            inverse_move = pay_move.copy({"date": fields.Date.today()})
            inverse_move.line_ids.write({"date_maturity": fields.Date.today()})
            for line in inverse_move.line_ids:
                if line.debit > 0:
                    line.write(
                        {
                            "account_id": inverse_debit_account,
                            "analytic_account_id": False,
                        }
                    )
                elif line.credit > 0:
                    line.write(
                        {
                            "account_id": inverse_credit_account,
                            "analytic_account_id": analytic,
                            "analytic_tag_ids": [(4, analytic_tag)] if analytic_tag else False
                        }
                    )
            inverse_move.action_post()
            gift.inverse_payment_id = inverse_move

        notify_ids = self.env["res.config.settings"].get_param("gift_notify_ids")
        if notify_ids:
            for gift in self:
                partner = gift.partner_id
                child = gift.child_id
                values = {
                    "name": partner.name,
                    "ref": partner.ref,
                    "child_name": child.name,
                    "child_code": child.local_id,
                    "reason": gift.undeliverable_reason,
                }
                body = (
                    "{name} ({ref}) made a gift to {child_name}"
                    " ({child_code}) which is undeliverable because {reason}."
                    "\nPlease inform the sponsor about it."
                ).format(**values)
                gift.message_post(
                    body=body,
                    subject=_("Gift Undeliverable Notification"),
                    partner_ids=notify_ids,
                    subtype_xmlid="mail.mt_comment",
                )
