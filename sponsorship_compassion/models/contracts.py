##############################################################################
#
#    Copyright (C) 2014-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import json
import logging
import os
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

from odoo.addons.child_compassion.models.compassion_hold import HoldType

from .product_names import (
    BIRTHDAY_GIFT,
    CHRISTMAS_GIFT,
    GIFT_CATEGORY,
    GIFT_PRODUCTS_REF,
    PRODUCT_GIFT_CHRISTMAS,
)

logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)
testing = tools.config.get("test_enable")
SPONSORSHIP_TYPE_LIST = ["S", "SC", "SWP"]


class SponsorshipContract(models.Model):
    _inherit = ["recurring.contract", "compassion.mapped.model"]
    _name = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    correspondent_id = fields.Many2one(
        "res.partner",
        string="Correspondent",
        tracking=True,
        index=True,
        readonly=False,
    )
    partner_codega = fields.Char(
        "Partner ref", related="correspondent_id.ref", readonly=True
    )
    fully_managed = fields.Boolean(compute="_compute_fully_managed", store=True)
    birthday_invoice = fields.Float(
        "Annual birthday gift",
        help="Set the amount to enable automatic invoice creation each year "
        "for a birthday gift. The invoice is set two months before "
        "child's birthday.",
        tracking=True,
    )
    christmas_invoice = fields.Float(
        "Annual christmas gift",
        help="Set the amount to enable automatic invoice creation each year "
        "for a christmas gift. The invoice is set depending christmas invoice setting",
        tracking=True,
    )
    reading_language = fields.Many2one(
        "res.lang.compassion",
        "Preferred language",
        tracking=True,
        readonly=False,
    )
    transfer_partner_id = fields.Many2one(
        "compassion.global.partner", "Transferred to", readonly=False
    )
    gmc_commitment_id = fields.Char(
        help="Connect global ID", readonly=True, copy=False, tracking=True
    )
    hold_expiration_date = fields.Datetime(
        help="Used for setting a hold after sponsorship cancellation"
    )
    send_gifts_to = fields.Selection(
        [("partner_id", "Payer"), ("correspondent_id", "Correspondent")],
        default="correspondent_id",
    )
    gift_partner_id = fields.Many2one(
        "res.partner", compute="_compute_gift_partner", readonly=False
    )
    contract_line_ids = fields.One2many(
        default=lambda self: self._get_standard_lines(), readonly=False
    )
    preferred_name = fields.Char(related="child_id.preferred_name")

    child_id = fields.Many2one(
        "compassion.child",
        "Sponsored child",
        readonly=True,
        copy=False,
        states={
            "draft": [("readonly", False)],
            "waiting": [("readonly", False)],
            "mandate": [("readonly", False)],
        },
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    project_id = fields.Many2one(
        "compassion.project", "Project", related="child_id.project_id", readonly=False
    )
    child_name = fields.Char(
        "Sponsored child name", related="child_id.name", readonly=True
    )
    child_code = fields.Char(
        "Sponsored child code", related="child_id.local_id", readonly=True, store=True
    )
    is_active = fields.Boolean(
        "Contract Active",
        compute="_compute_active",
        store=True,
        help="It indicates that the first invoice has been paid and the "
        "contract was activated.",
    )
    # Field used for identifying gifts from sponsor
    commitment_number = fields.Integer(copy=False)
    origin_id = fields.Many2one(
        "recurring.contract.origin",
        "Origin",
        ondelete="restrict",
        tracking=True,
        index=True,
        readonly=False,
    )
    parent_id = fields.Many2one(
        "recurring.contract",
        "Previous sponsorship",
        tracking=True,
        index=True,
        copy=False,
        readonly=False,
    )
    sub_sponsorship_id = fields.Many2one(
        "recurring.contract", "sub sponsorship", readonly=True, copy=False, index=True
    )
    partner_lang = fields.Selection(
        string="Partner language", related="partner_id.lang", store=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
        readonly=False,
        states={"terminated": [("readonly", True)]},
        ondelete="restrict",
        tracking=True,
    )
    gmc_payer_partner_id = fields.Many2one(
        "res.partner", readonly=True, help="Partner synchronized with GMC as a payer."
    )
    gmc_correspondent_commitment_id = fields.Char(
        readonly=True, help="Id of the correspondent commitment.", tracking=True
    )
    type = fields.Selection(
        [
            ("O", "General"),
            ("G", "Child Gift"),
            ("S", "Sponsorship"),
            ("SC", "Correspondence"),
            ("SWP", "Write&Pray"),
        ],
        required=True,
        default="O",
    )
    group_freq = fields.Char(
        string="Payment frequency", compute="_compute_frequency", readonly=True
    )
    is_first_sponsorship = fields.Boolean(
        compute="_compute_is_first_sponsorship", store=True
    )
    sponsorship_line_id = fields.Integer(
        help="Identifies the active sponsorship line of a sponsor."
        "When sponsorship is ended but a SUB is made, the SUB will have"
        "the same line id. Only new sponsorships will have new ids."
    )
    contract_duration = fields.Integer(
        compute="_compute_contract_duration", help="Contract duration in days"
    )
    hold_id = fields.Many2one(
        "compassion.hold", related="child_id.hold_id", readonly=False
    )
    can_make_gift = fields.Boolean(
        compute="_compute_can_make_gift",
        help="Whether gift to the child is possible at the moment or not",
    )
    can_write_letter = fields.Boolean(
        compute="_compute_can_write_letter",
        help="Whether letter to the child is possible at the moment or not",
    )
    is_direct_debit = fields.Boolean(
        compute="_compute_is_direct_debit", help="Is paid by direct debit"
    )
    is_gift_authorized = fields.Boolean(compute="_compute_is_gift_auth")

    _sql_constraints = [
        (
            "unique_gmc_commitment_id",
            "unique(gmc_commitment_id)",
            "You cannot have same commitment ids for contracts",
        )
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_standard_lines(self):
        if "S" in self.env.context.get("default_type", "O"):
            return self._get_sponsorship_standard_lines(False)
        return []

    @api.onchange("company_id", "pricelist_id")
    def _get_correct_pricelist(self):
        if "S" in self.env.context.get("default_type", "O"):
            self.contract_line_ids = self._get_sponsorship_standard_lines(False)

    @api.onchange("type")
    def _create_empty_lines_for_correspondence(self):
        self.contract_line_ids = self._get_sponsorship_standard_lines(
            self.type in ["SC", "SWP"]
        )

    @api.model
    def _get_sponsorship_standard_lines(self, correspondence):
        """Select Sponsorship and General Fund by default"""
        res = [(5, 0, 0)]
        sponsorship_product = self.env["product.template"].search(
            [
                ("default_code", "=", "sponsorship"),
            ]
        )
        gen_product = self.env["product.template"].search(
            [
                ("default_code", "=", "fund_gen"),
            ]
        )

        if not len(sponsorship_product) == 1:
            raise ValidationError(
                _(
                    "The sponsorship product does not exist for the "
                    "current company yet. Please create a product with "
                    "default_code 'sponsorship' first."
                )
            )

        if not len(gen_product) == 1:
            raise ValidationError(
                _(
                    "The donation product does not exist for the "
                    "current company yet. Please create a product with "
                    "default_code 'fund_gen' first."
                )
            )

        sponsorship_product = sponsorship_product.product_variant_id
        gen_product = gen_product.product_variant_id
        if self.company_id:
            pricelist = self.pricelist_id
            sponsorship_product.with_context(
                {"pricelist": pricelist.id, "partner": self.partner_id.id}
            )._compute_product_price()
            gen_product.with_context(
                {"pricelist": pricelist.id, "partner": self.partner_id.id}
            )._compute_product_price()

        sponsorship_vals = {
            "product_id": sponsorship_product.id,
            "quantity": 0 if correspondence else 1,
            "amount": 0 if correspondence else sponsorship_product.list_price,
            "subtotal": 0 if correspondence else sponsorship_product.list_price,
        }
        res.append((0, 0, sponsorship_vals))
        # Avoid appending the GEN fund when one line already exists
        # (the partner most probably doesn't want it)
        if len(self.contract_line_ids) != 1:
            gen_vals = {
                "product_id": gen_product.id,
                "quantity": 0 if correspondence else 1,
                "amount": 0 if correspondence else gen_product.list_price,
                "subtotal": 0 if correspondence else gen_product.list_price,
            }
            res.append((0, 0, gen_vals))
        return res

    @api.depends("partner_id", "correspondent_id")
    def _compute_fully_managed(self):
        """Tells if the correspondent and the payer is the same person."""
        for contract in self:
            contract.fully_managed = contract.partner_id == contract.correspondent_id

    def _compute_last_paid_invoice(self):
        """Override to exclude gift invoices."""
        for contract in self:
            contract.last_paid_invoice_date = max(
                contract.invoice_line_ids.with_context(lang="en_US")
                .filtered(
                    lambda line: line.payment_state == "paid"
                    and line.product_id.categ_name != GIFT_CATEGORY
                )
                .mapped("move_id.invoice_date")
                or [False]
            )

    def _compute_invoices(self):
        super()._compute_invoices()
        # For some cases we only want to consider sponsorship invoices and exclude
        # all gifts and fund donations
        if self.env.context.get("open_invoices_sponsorship_only"):
            for contract in self:
                contract.open_invoice_ids = contract.open_invoice_ids.filtered(
                    lambda i: i.invoice_category == "sponsorship"
                )
        # For some cases we want to get only the gift or fund invoices
        # (birthday, christmas)
        if self.env.context.get("open_invoices_exclude_sponsorship"):
            for contract in self:
                contract.open_invoice_ids = contract.open_invoice_ids.filtered(
                    lambda i: i.invoice_category != "sponsorship"
                )
        gift_contracts = self.filtered(lambda c: c.type == "G")
        for contract in gift_contracts:
            invoices = contract.mapped(
                "contract_line_ids.sponsorship_id.invoice_line_ids.move_id"
            )
            gift_invoices = invoices.filtered(
                lambda i: i.invoice_category == "gift"
                and i.state not in ("cancel", "draft")
            )
            contract.nb_invoices += len(gift_invoices)

    def _compute_gift_partner(self):
        for contract in self:
            contract.gift_partner_id = getattr(
                contract, contract.send_gifts_to, contract.correspondent_id
            )

    def _compute_contract_products(self):
        if not self.env.context.get("open_invoices_exclude_sponsorship"):
            super()._compute_contract_products()
        else:
            # Special case where we consider only gift products
            for contract in self:
                contract.product_ids = self.env["product.product"]
                if contract.birthday_invoice:
                    contract.product_ids += self.env["product.product"].search(
                        [("default_code", "=", GIFT_PRODUCTS_REF[0])]
                    )
                if contract.christmas_invoice:
                    contract.product_ids += self.env["product.product"].search(
                        [("default_code", "=", PRODUCT_GIFT_CHRISTMAS)]
                    )

    @api.depends("partner_id", "partner_id.ref", "child_id", "child_id.local_id")
    def name_get(self):
        """Gives a friendly name for a sponsorship"""
        result = []
        for contract in self:
            if contract.partner_id.ref or contract.reference:
                name = contract.partner_id.ref or contract.reference
                if contract.child_id:
                    name += " - " + contract.child_code
                elif contract.contract_line_ids:
                    name += " - " + contract.contract_line_ids[0].product_id.name
                result.append((contract.id, name))
        return result

    @api.depends("activation_date", "state")
    def _compute_active(self):
        for contract in self:
            contract.is_active = bool(
                contract.activation_date
            ) and contract.state not in ("terminated", "cancelled")

    def _compute_frequency(self):
        frequencies = {
            "1 month": _("Monthly"),
            "2 month": _("Bimonthly"),
            "3 month": _("Quarterly"),
            "4 month": _("Four-monthly"),
            "6 month": _("Bi-annual"),
            "12 month": _("Annual"),
            "1 year": _("Annual"),
        }
        for contract in self:
            if contract.type == "S":
                recurring_value = contract.group_id.advance_billing_months
                recurring_unit = "month"
            else:
                recurring_value = contract.group_id.recurring_value
                recurring_unit = contract.group_id.recurring_unit
            frequency = f"{recurring_value} {recurring_unit}"
            if frequency in frequencies:
                frequency = frequencies[frequency]
            else:
                frequency = _("every") + " " + frequency.lower()
            contract.group_freq = frequency

    def _compute_contract_duration(self):
        for contract in self:
            if not contract.activation_date:
                contract.contract_duration = 0
            else:
                contract_start_date = contract.activation_date
                end_date = contract.end_date if contract.end_date else datetime.now()
                contract.contract_duration = (end_date - contract_start_date).days

    @api.constrains("parent_id")
    def check_unique_sub_sponsorship(self):
        for sponsorship in self:
            parent = sponsorship.parent_id
            if parent:
                same_parent = self.search_count(
                    [
                        ("parent_id", "=", parent.id),
                        ("state", "not in", ["cancelled", "terminated"]),
                    ]
                )
                if same_parent > 1:
                    raise ValidationError(
                        _(
                            "Unfortunately this sponsorship is already used, "
                            "please choose a unique one"
                        )
                    )

    def _compute_can_make_gift(self):
        days_allowed = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sponsorship_compassion.time_allowed_for_gifts", 90)
        )
        now = fields.Datetime.now()
        for sponsorship in self:
            hold_gifts = sponsorship.project_id.hold_gifts and not self.env.context.get(
                "allow_during_suspension"
            )
            is_allowed = (
                sponsorship.state not in ["terminated", "cancelled", "draft"]
                and not hold_gifts
            )
            if sponsorship.state == "terminated" and not hold_gifts:
                is_allowed = (now - sponsorship.end_date).days <= int(days_allowed)
            sponsorship.can_make_gift = is_allowed

    def _compute_can_write_letter(self):
        days_allowed = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sponsorship_compassion.time_allowed_for_letters", 90)
        )
        now = fields.Datetime.now()
        for sponsorship in self:
            hold_letters = (
                sponsorship.project_id.hold_s2b_letters
                and not self.env.context.get("allow_during_suspension")
            )
            is_allowed = (
                sponsorship.state not in ["terminated", "cancelled", "draft"]
                and not hold_letters
            )
            if sponsorship.state == "terminated" and not hold_letters:
                is_allowed = (now - sponsorship.end_date).days <= int(days_allowed)
            sponsorship.can_write_letter = is_allowed

    def _filter_due_invoices(self):
        # Gifts should not be counted in due invoices
        # Fund-suspended projects are also excluded
        # Correspondence and gift contracts are also excluded
        valid_contracts = self.filtered(
            lambda s: s.type in ("S", "O") and not s.child_id.project_id.hold_cdsp_funds
        )
        invoices = super(SponsorshipContract, valid_contracts)._filter_due_invoices()
        return invoices.filtered(lambda i: i.invoice_category != "gift")

    def _compute_is_direct_debit(self):
        dd_modes = self.env["account.payment.mode"].search(
            [("payment_method_code", "like", "%direct_debit")]
        )
        for contract in self:
            contract.is_direct_debit = contract.payment_mode_id in dd_modes

    @api.depends("payment_mode_id")
    def _compute_is_gift_auth(self):
        for contract in self:
            contract.is_gift_authorized = True
            if not contract.is_direct_debit and (
                contract.birthday_invoice or contract.christmas_invoice
            ):
                contract.is_gift_authorized = False

    @api.depends("correspondent_id")
    def _compute_is_first_sponsorship(self):
        for sponsorship in self:
            old_sponsorships = sponsorship.correspondent_id.sponsorship_ids.filtered(
                lambda c, sponsorship=sponsorship: c.state != "cancelled"
                and c.start_date
                and c.start_date < (sponsorship.start_date or sponsorship.create_date)
            )
            sponsorship.is_first_sponsorship = not old_sponsorships

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    @api.model
    def create(self, vals):
        """Perform various checks on contract creations"""
        # Force the commitment_number
        partner_ids = []
        partner_id = vals.get("partner_id")
        if partner_id:
            partner_ids.append(partner_id)
        correspondent_id = vals.get("correspondent_id")
        if correspondent_id and correspondent_id != partner_id:
            partner_ids.append(correspondent_id)
        if partner_ids:
            other_nums = self.search(
                [
                    "|",
                    ("partner_id", "in", partner_ids),
                    ("correspondent_id", "in", partner_ids),
                    ("state", "not in", ["cancelled", "terminated"]),
                ]
            ).mapped("commitment_number")
            vals["commitment_number"] = max(other_nums or [0]) + 1
        else:
            vals["commitment_number"] = 1

        child = self.env["compassion.child"].browse(vals.get("child_id"))
        sponsor_id = vals.get("correspondent_id", vals.get("partner_id"))
        if "S" in vals.get("type", "") and child and sponsor_id:
            child.with_context({}).child_sponsored(sponsor_id)

        # Generates commitment number for contracts BVRs
        if "commitment_number" not in vals:
            partner_id = vals.get("partner_id")
            correspondent_id = vals.get("correspondent_id", partner_id)
            if partner_id:
                other_nums = self.search(
                    [
                        "|",
                        "|",
                        "|",
                        ("partner_id", "=", partner_id),
                        ("partner_id", "=", correspondent_id),
                        ("correspondent_id", "=", partner_id),
                        ("correspondent_id", "=", correspondent_id),
                    ]
                ).mapped("commitment_number")

                vals["commitment_number"] = max(other_nums or [-1]) + 1
            else:
                vals["commitment_number"] = 1

        new_sponsorship = super().create(vals)

        # Set the sub_sponsorship_id in the current parent_id and take
        # sponsorship line id
        if "parent_id" in vals and vals["parent_id"]:
            sponsorship = self.env["recurring.contract"].browse(vals["parent_id"])

            sponsorship.sub_sponsorship_id = new_sponsorship
            new_sponsorship.sponsorship_line_id = sponsorship.sponsorship_line_id

        return new_sponsorship

    def write(self, vals):
        """Perform various checks on contract modification"""
        if "child_id" in vals:
            self._link_unlink_child_to_sponsor(vals)

        old_partners = self.env["res.partner"]
        if "partner_id" in vals:
            old_partners = self.mapped("partner_id")
        if "correspondent_id" in vals:
            old_partners |= self.mapped("correspondent_id")

        # Change the sub_sponsorship_id value in the previous parent_id
        if "parent_id" in vals:
            self.mapped("parent_id").write({"sub_sponsorship_id": False})

        super().write(vals)

        updated_correspondents = self.env[self._name]
        previous_states = []
        if "correspondent_id" in vals:
            previous_states.extend([r.state for r in self])
            updated_correspondents = self.filtered("gmc_commitment_id")
            # Update the correspondent in GMC
            if not self.env.context.get("no_upsert"):
                for record in updated_correspondents:
                    record._change_correspondent()
            for child in self.mapped("child_id"):
                child.child_sponsored(vals["correspondent_id"])

        if "reading_language" in vals:
            (self - updated_correspondents)._on_language_changed()

        if old_partners:
            self.mapped("partner_id").update_number_sponsorships()
            old_partners.update_number_sponsorships()

        # Set the sub_sponsorship_id in the current parent_id
        if "parent_id" in vals:
            for sponsorship in self.filtered("parent_id"):
                parent = sponsorship.parent_id
                parent.sub_sponsorship_id = sponsorship
                sponsorship.sponsorship_line_id = parent.sponsorship_line_id

        if any([k in vals for k in ["partner_id", "correspondent_id"]]):
            self.on_change_partner_correspondent_id()
            self.auto_correspondent_id()

        return True

    def unlink(self):
        for contract in self:
            # We can only delete draft sponsorships.
            if (
                "S" in contract.type
                and contract.state != "draft"
                and not self.env.context.get("force_delete")
            ):
                raise UserError(_("You cannot delete a validated sponsorship."))
            # Remove sponsor of child and release it
            if "S" in contract.type and contract.child_id:
                if contract.child_id.sponsor_id == contract.correspondent_id:
                    contract.child_id.with_context({}).child_unsponsored()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def _on_invoice_line_removal(self, invl_rm_data):
        pass

    def commitment_sent(self, vals):
        """Called when GMC received the commitment."""
        self.ensure_one()
        # We don't need to write back partner and child
        vals.pop("child_id", False)
        vals.pop("correspondent_id", False)
        vals["state"] = "active"
        self.write(vals)
        # Remove the hold on the child.
        for sponsorship in self.filtered("hold_id"):
            sponsorship.hold_id.state = "expired"
            sponsorship.child_id.hold_id = False
        # Force refresh some fields in case they are not in sync
        self.mapped("partner_id").update_number_sponsorships()
        self._compute_active()
        return True

    def correspondence_updated(self, vals):
        # Called after answer from GMC when changing the correspondent
        self.write(
            {"gmc_correspondent_commitment_id": vals["gmc_correspondent_commitment_id"]}
        )
        self.correspondent_id.update_number_sponsorships()
        return True

    def cancel_sent(self, vals):
        """Called when GMC received the commitment cancel request."""
        self.ensure_one()
        hold_id = vals.get("hold_id")
        hold = self.env["compassion.hold"].search(
            ["|", ("hold_id", "=", hold_id), ("id", "=", hold_id)]
        )
        if (
            self.hold_expiration_date
            and self.hold_expiration_date > fields.Datetime.now()
        ):
            hold_expiration = self.hold_expiration_date
            child = self.child_id
            hold.write(
                {
                    "child_id": child.id,
                    "type": HoldType.SPONSOR_CANCEL_HOLD.value,
                    "channel": "sponsor_cancel",
                    "expiration_date": hold_expiration,
                    "primary_owner": self.write_uid.id,
                    "state": "active",
                }
            )
            if not child.hold_id:
                child.hold_id = hold
        return True

    def put_child_on_no_money_hold(self):
        """Convert child to No Money Hold"""
        self.ensure_one()
        return self.hold_id.write(
            {
                "expiration_date": self.env[
                    "compassion.hold"
                ].get_default_hold_expiration(HoldType.NO_MONEY_HOLD),
                "type": HoldType.NO_MONEY_HOLD.value,
            }
        )

    @api.onchange("partner_id")
    def auto_correspondent_id(self):
        """If correspondent is not specified use partner_id"""
        if self.partner_id and not self.correspondent_id:
            self.correspondent_id = self.partner_id

    def on_change_partner_correspondent_id(self):
        """On partner change, we set the new commitment number
        (for gift identification)."""
        partners = self.partner_id + self.correspondent_id
        contracts = self.search(
            [
                "|",
                ("partner_id", "in", partners.ids),
                ("correspondent_id", "in", partners.ids),
                ("state", "not in", ["terminated", "cancelled"]),
            ]
        )
        self.commitment_number = max(contracts.mapped("commitment_number") or [0]) + 1

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def open_invoices(self):
        res = super().open_invoices()
        if self.type == "G":
            # Include gifts of related sponsorship for gift contracts
            sponsorship_invoices = self.mapped(
                "contract_line_ids.sponsorship_id.invoice_line_ids.move_id"
            )
            gift_invoices = sponsorship_invoices.filtered(
                lambda i: i.invoice_category == "gift"
            )
            res["domain"] = [("id", "in", gift_invoices.ids)]
        return res

    @api.onchange("parent_id")
    def on_change_parent_id(self):
        """If a previous sponsorship is selected, the origin should be
        SUB Sponsorship."""
        if self.parent_id:
            self.origin_id = self.parent_id.origin_id.id

    def open_contract(self):
        """Used to bypass opening a contract in popup mode from
        res_partner view."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contract",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "current",
            "context": self.with_context(default_type=self.type).env.context,
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_active(self):
        """Hook for doing something when contract is activated.
        Update child to mark it has been sponsored,
        and activate gift contracts.
        Send messages to GMC.
        """
        not_active = self.filtered(lambda c: not c.is_active)
        if not_active:
            not_active.write({"activation_date": fields.Datetime.now()})
        self.write({"state": "active"})
        last_line_id = self.search(
            [("sponsorship_line_id", "!=", False)],
            order="sponsorship_line_id desc",
            limit=1,
        ).sponsorship_line_id

        # Write payment term in partner property and sponsorship line id
        for contract in self:
            contract.partner_id.customer_payment_mode_id = contract.payment_mode_id
            if contract.child_id and not contract.sponsorship_line_id:
                last_line_id += 1
                contract.sponsorship_line_id = last_line_id

        # Cancel the old invoices if a contract is activated
        delay = datetime.now() + relativedelta(seconds=30)
        self.with_delay(eta=delay).cancel_old_invoices()

        con_line_obj = self.env["recurring.contract.line"]
        for contract in self.filtered(lambda c: c.type in SPONSORSHIP_TYPE_LIST):
            gift_contract_lines = con_line_obj.search(
                [("sponsorship_id", "=", contract.id)]
            )
            gift_contracts = gift_contract_lines.mapped("contract_id")
            if gift_contracts:
                gift_contracts.contract_active()

        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        partners.update_number_sponsorships()
        # Creating the messages to send to GMC when a sponsorship is activated
        for contract in self.filtered(lambda c: c.type in SPONSORSHIP_TYPE_LIST):
            # Define the payer that will be sync to gmc
            contract.gmc_payer_partner_id = contract.partner_id
            # UpsertConstituent Message
            partner = contract.correspondent_id
            partner.upsert_constituent()
            contract.upsert_sponsorship()
        return True

    def _contract_cancelled(self, vals):
        super()._contract_cancelled(vals)
        self.filtered(
            lambda c: c.type in SPONSORSHIP_TYPE_LIST
        )._on_sponsorship_finished()
        return True

    def _contract_terminated(self, vals):
        super()._contract_terminated(vals)
        self.filtered(
            lambda c: c.type in SPONSORSHIP_TYPE_LIST
        )._on_sponsorship_finished()
        return True

    def contract_waiting(self):
        contracts = self.filtered(lambda c: c.type == "O")
        super().contract_waiting()
        for contract in self - contracts:
            if not contract.start_date:
                contract.start_date = fields.Datetime.now()

            if contract.type == "G":
                # Activate directly if sponsorship is already active
                for line in contract.contract_line_ids:
                    sponsorship = line.sponsorship_id
                    if sponsorship.state == "active":
                        contract.contract_active()
            elif contract.type == "S" or (
                contract.type in ["SC", "SWP"] and contract.total_amount > 0
            ):
                # Update the expiration date of the No Money Hold
                hold = contract.hold_id
                hold.write(
                    {
                        "expiration_date": hold.get_default_hold_expiration(
                            HoldType.NO_MONEY_HOLD
                        )
                    }
                )
                if contract.total_amount == 0:
                    raise UserError(
                        _("You cannot validate a sponsorship without any amount")
                    )
                contract.state = "waiting"
            elif contract.type in ["SC", "SWP"]:
                # Activate directly correspondence sponsorships
                contract.contract_active()
        return True

    def action_cancel_draft(self):
        """Set back a cancelled contract to draft state."""
        super().action_cancel_draft()
        for contract in self.filtered("child_id"):
            if contract.child_id.is_available:
                contract.child_id.child_sponsored(contract.correspondent_id.id)
            else:
                contract.child_id = False
        return True

    def upsert_sponsorship(self):
        """Creates and returns upsert messages for sponsorships."""
        messages = self.env["gmc.message"]
        action = self.env.ref("sponsorship_compassion.create_sponsorship")
        if self.env.context.get("no_upsert"):
            return messages
        for sponsorship in self:
            messages += messages.create(
                {
                    "action_id": action.id,
                    "child_id": sponsorship.child_id.id,
                    "partner_id": sponsorship.correspondent_id.id,
                    "object_id": sponsorship.id,
                }
            )
        return messages

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _on_language_changed(self):
        """Update the preferred language in GMC."""
        messages = self.upsert_sponsorship().with_context({"async_mode": False})
        error_msg = (
            "Error when updating sponsorship language. "
            "You may be out of sync with GMC - please try again."
        )
        for message in messages:
            try:
                message.process_messages()
                if "failure" in message.state:
                    failure = message.failure_reason or error_msg
                    self.env.user.notify_danger(failure, "Language update failed.")
            except Exception:
                self.env.user.notify_danger(error_msg, "Language update failed.")
                logger.error(error_msg, exc_info=True)

    def _change_correspondent(self):
        self.ensure_one()
        if not self.correspondent_id.global_id:
            self.correspondent_id.upsert_constituent().process_messages()
        message_obj = self.env["gmc.message"].with_context({"async_mode": False})
        upsert_correspondent_gmc = self.env.ref(
            "sponsorship_compassion.upsert_correspondent_commitment"
        )

        if self.state in ("cancelled", "terminated"):
            raise UserError(
                _(
                    "You can't change the correspondent of a"
                    " cancelled or terminated sponsorship"
                )
            )

        message = message_obj.create(
            {
                "action_id": upsert_correspondent_gmc.id,
                "child_id": self.child_id.id,
                "partner_id": self.correspondent_id.id,
                "object_id": self.id,
            }
        )
        message.process_messages()

        answer = json.loads(message.answer)
        if not isinstance(answer, dict) or "Code" not in answer:
            raise UserError("Invalid GMC answer\n" f"Answer : {answer}")
        if message.state == "failure":
            error_message = answer["Message"]
            logger.error(message.failure_reason)
            raise UserError(_("GMC returned an error :") + "\n" + error_message)
        elif message.state == "odoo_failure":
            logger.warning(message.failure_reason)
        return True

    def add_correspondent(self):
        self.ensure_one()
        self.correspondent_id.upsert_constituent().process_messages()

        # Create new sponsorships at GMC
        message = self.upsert_sponsorship()
        message.with_context({"async_mode": False}).process_messages()

        answer = json.loads(message.answer)
        if not isinstance(answer, dict) or "Message" not in answer:
            return False, _("Invalid GMC answer")
        if "failure" in message.state:
            error_message = answer["Message"]
            logger.error(error_message)
            return (
                False,
                _(
                    "Couldn't activate the new correspondent, GMC returned "
                    "the following error: "
                )
                + "\n"
                + error_message,
            )

        self.correspondent_id.update_number_sponsorships()
        return True, ""

    def _on_sponsorship_finished(self):
        """Called when a sponsorship is terminated or cancelled:
        Terminate related gift contracts and sync with GMC.
        """
        departure = self.env.ref("sponsorship_compassion.end_reason_depart")
        for sponsorship in self:
            gift_contract_lines = self.env["recurring.contract.line"].search(
                [("sponsorship_id", "=", sponsorship.id)]
            )
            for line in gift_contract_lines:
                contract = line.contract_id
                if len(contract.contract_line_ids) > 1:
                    line.unlink()
                else:
                    contract.action_contract_terminate()

            if sponsorship.gmc_commitment_id and sponsorship.end_reason_id != departure:
                # Cancel Sponsorship Message
                message_obj = self.env["gmc.message"]
                action_id = self.env.ref("sponsorship_compassion.cancel_sponsorship").id

                message_vals = {
                    "action_id": action_id,
                    "object_id": sponsorship.id,
                    "partner_id": sponsorship.correspondent_id.id,
                    "child_id": sponsorship.child_id.id,
                }
                message_obj.create(message_vals)
            elif not sponsorship.gmc_commitment_id:
                # Remove CreateSponsorship message.
                message_obj = self.env["gmc.message"]
                action_id = self.env.ref("sponsorship_compassion.create_sponsorship").id
                message_obj.search(
                    [
                        ("action_id", "=", action_id),
                        ("state", "in", ["new", "failure", "odoo_failure"]),
                        ("object_id", "=", sponsorship.id),
                    ]
                ).unlink()
                sponsorship.state = "cancelled"
        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        partners.update_number_sponsorships()

    def _link_unlink_child_to_sponsor(self, vals):
        """Link/unlink child to sponsor"""
        child_id = vals.get("child_id")
        for contract in self:
            if (
                contract.type in SPONSORSHIP_TYPE_LIST
                and contract.child_id
                and contract.child_id.id != child_id
            ):
                # Free the previously selected child
                contract.child_id.child_unsponsored()
            if child_id and contract.type in SPONSORSHIP_TYPE_LIST:
                # Mark the selected child as sponsored
                self.env["compassion.child"].browse(child_id).child_sponsored(
                    vals.get("correspondent_id") or contract.correspondent_id.id
                )

    def _generate_gifts(self, invoicer, gift_type):
        """Creates the annual gifts for sponsorships that
        have set the option for automatic birthday or Christmas gifts creation."""
        logger.debug(f"Automatic {gift_type} Gift Generation Started.")
        # Search active Sponsorships with automatic birthday gift
        contracts = self

        product_id = (
            self.env["product.product"]
            .search(
                [
                    (
                        "default_code",
                        "=",
                        GIFT_PRODUCTS_REF[0]
                        if gift_type == BIRTHDAY_GIFT
                        else PRODUCT_GIFT_CHRISTMAS,
                    )
                ],
                limit=1,
            )
            .id
        )

        due_dates = {}  # Dict to store the due dates of the contracts

        # Don't generate gift for contract that are holding gifts or if they
        # don't have an amount for the gift
        for contract in contracts:
            if (
                contract.project_id.hold_gifts
                or eval(f"contract.{gift_type}_invoice") <= 0
            ):
                contracts -= contract
                continue

            # checks if there is already a gift for this year which has been cancelled
            current_year = fields.Datetime.now().year
            start_of_year = fields.Datetime.from_string(
                f"{current_year}-01-01 00:00:00"
            )
            end_of_year = fields.Datetime.from_string(f"{current_year}-12-31 23:59:59")
            gift_this_year = self.env["account.move.line"].search(
                [
                    ("partner_id", "=", contract.partner_id.id),
                    ("product_id", "=", product_id),
                    ("date", ">=", start_of_year),
                    ("date", "<=", end_of_year),
                    ("parent_state", "=", "cancel"),
                    ("contract_id", "=", contract.id),
                ]
            )
            if gift_this_year:
                contracts -= contract
                continue

            # Checks if we need to generate the birthday gifts or the Christmas gifts
            current_date = date.today()
            if gift_type == BIRTHDAY_GIFT and contract.child_id.birthdate:
                event_date = contract.child_id.birthdate
                event_bascule_date = self._get_bascule_date(contract, event_date)

                # We only generate the birthday gift if the current date
                # is between 3 months and 2 weeks before the bascule date
                if (
                    event_bascule_date + relativedelta(months=-3)
                    <= current_date
                    <= event_bascule_date + relativedelta(weeks=-2)
                ):
                    due_dates[contract] = event_bascule_date
                else:
                    contracts -= contract
            elif gift_type == CHRISTMAS_GIFT:  # case of Christmas gift
                christ_inv_due = int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("sponsorship_compassion.christmas_inv_due_month", 10)
                )

                if current_date.month == christ_inv_due:
                    # Here we generate the Christmas gifts only if we are in the month
                    # defined in sponsorship_compassion.christmas_inv_due_month
                    due_dates[contract] = self._get_bascule_date(contract, current_date)
                else:
                    contracts -= contract
            else:
                contracts -= contract

        if contracts:
            total = str(len(contracts))
            logger.debug(f"Found {total} {gift_type} Gifts to generate.")

            gift_wizard = (
                self.env["generate.gift.wizard"]
                .with_context(recurring_invoicer_id=invoicer.id)
                .create(
                    {
                        "description": f"Automatic {gift_type} gift",
                        "product_id": product_id,
                        "amount": 0.0,
                        "contract_id": 0,
                    }
                )
            )

            # Generate invoices
            count = 1
            for contract in contracts:
                logger.debug(f"{gift_type} Gift Generation: {count}/{total} ")
                self._generate_gift(
                    gift_wizard,
                    contract,
                    invoicer,
                    gift_type,
                    due_date=due_dates[contract],
                )
                count += 1

        logger.debug(f"Automatic {gift_type} Gift Generation Finished !!")
        return True

    def _generate_gift(self, gift_wizard, contract, invoicer, gift_type, due_date=None):
        gift_wizard.write(
            {
                "amount": eval(f"contract.{gift_type}_invoice"),
                "contract_id": contract.id,
            }
        )
        gift_wizard.with_context(invoicer=invoicer).generate_invoice(due_date=due_date)

    def invoice_paid(self, invoice):
        """Prevent to reconcile invoices for sponsorships older than 6 months."""
        bypass_state = self.env.context.get("bypass_state", False)
        for invl in invoice.invoice_line_ids:
            if invl.contract_id and invl.contract_id.child_id:
                contract = invl.contract_id

                # Check contract is active or terminated recently.
                if contract.state == "cancelled" and not bypass_state:
                    raise UserError(f"The contract {contract.name} is not active.")
                if (
                    contract.state == "terminated"
                    and contract.end_date
                    and not bypass_state
                ):
                    limit = invoice.invoice_date - relativedelta(days=180)
                    ended_since = contract.end_date
                    if ended_since.date() < limit:
                        raise UserError(f"The contract {contract.name} is not active.")

                # Activate gift related contracts (if any)
                if "S" in contract.type:
                    gift_contract_lines = self.env["recurring.contract.line"].search(
                        [
                            ("sponsorship_id", "=", contract.id),
                            ("contract_id.state", "=", "waiting"),
                        ]
                    )
                    if gift_contract_lines:
                        gift_contract_lines.mapped("contract_id").contract_active()

                if (
                    len(
                        contract.invoice_line_ids.filtered(
                            lambda i: i.payment_state == "paid"
                        )
                    )
                    == 1
                ):
                    contract.partner_id.set_privacy_statement(origin="first_payment")

        # Super method will activate waiting contracts
        # Only activate sponsorships with sponsorship invoice
        to_activate = self
        if invoice.invoice_category != "sponsorship":
            to_activate -= self.filtered(lambda s: "S" in s.type)
        super(SponsorshipContract, to_activate).invoice_paid(invoice)

    @api.constrains("group_id")
    def _is_a_valid_group(self):
        for contract in self.filtered(lambda c: "S" in c.type):
            if (
                not contract.group_id.contains_sponsorship
                or contract.group_id.recurring_value != 1
            ):
                raise ValidationError(
                    _(
                        "You should select payment option with "
                        '"1 month" as recurring value'
                    )
                )
        return True

    def _get_filtered_invoice_lines(self, invoice_lines):
        # Exclude gifts from being cancelled
        res = invoice_lines.filtered(
            lambda invl: invl.contract_id.id in self.ids
            and invl.product_id.categ_name != GIFT_CATEGORY
        )
        return res

    def hold_gifts(self):
        """Hook for holding gifts."""
        pass

    def reactivate_gifts(self):
        """Hook for reactivating gifts."""
        pass

    def cancel_old_invoices(self):
        """Cancel the old open invoices of a contract
        which are older than the first paid invoice of contract.
        If the invoice has only one contract -> cancel
        Else -> draft to modify the invoice and validate
        """
        invoice_line_obj = self.env["account.move.line"]
        paid_invl = invoice_line_obj.search(
            [("contract_id", "in", self.ids), ("payment_state", "=", "paid")],
            order="due_date asc",
            limit=1,
        )
        invoice_lines = invoice_line_obj.search(
            [
                ("contract_id", "in", self.ids),
                ("payment_state", "=", "not_paid"),
                ("due_date", "<", paid_invl.due_date),
            ]
        )

        invoices = invoice_lines.mapped("move_id")

        for invoice in invoices:
            invoice_lines = invoice.invoice_line_ids

            inv_lines = self._get_filtered_invoice_lines(invoice_lines)

            if len(inv_lines) == len(invoice_lines):
                invoice.button_draft()
                invoice.button_cancel()
            else:
                invoice.button_draft()
                invoice.env.clear()
                inv_lines.unlink()
                invoice.action_post()

    def _updt_invoices_rc(self, vals):
        # Update only sponsorship invoices first, with invoice_lines and group changes
        # (handled in super)
        super(
            SponsorshipContract, self.with_context(open_invoices_sponsorship_only=True)
        )._updt_invoices_rc(vals)

        # Handle gifts if changes are made in those fields
        if "birthday_invoice" in vals or "christmas_invoice" in vals:
            contracts = self.with_context(open_invoices_exclude_sponsorship=True)
            gifts = contracts.mapped("open_invoice_ids")
            data_invs = gifts._build_invoices_data(contracts=contracts)
            if data_invs:
                gifts.update_open_invoices(data_invs)

    def _get_bascule_date(self, contract_inner, event_date_inner):
        """
        Compute the bascule date for the contract

        This function will compute the last possible day to be able to pay for the gift.
        It takes into account the block day as well as if the payment has to be made
        for the current month or the month before according to the company.
        For example if the event date is the 23rd october, the block day 15th,
        and we have to pay for previous month, the bascule date will be the 15th of
        september.

        :param contract_inner: The contract for which we want to compute the bascule
                               date
        :param event_date_inner: The date of the event
        :return: The bascule date
        """
        # Get the parameters to determine the bascule date
        company_id = contract_inner.company_id.id
        param_string = f"recurring_contract.do_generate_curr_month_{company_id}"
        curr_month = (
            self.env["ir.config_parameter"].sudo().get_param(param_string) == "True"
        )
        block_day_inner = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(f"recurring_contract.invoice_block_day_{company_id}", 31)
        )
        current_year = date.today().year
        if curr_month:
            event_date_inner = event_date_inner.replace(year=current_year)
            event_bascule_date_inner = event_date_inner.replace(day=block_day_inner)
        else:
            event_date_inner = event_date_inner.replace(year=current_year)
            event_bascule_date_inner = event_date_inner.replace(
                day=block_day_inner
            ) - relativedelta(months=1)

        # If the bascule date is after the event date,
        # the true bascule date is 1 month before
        if event_bascule_date_inner > event_date_inner:
            event_bascule_date_inner -= relativedelta(months=1)

        return event_bascule_date_inner
