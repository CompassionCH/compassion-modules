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
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.addons.child_compassion.models.compassion_hold import HoldType

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.recurring_contract.models.product_names import GIFT_PRODUCTS_REF, CHRISTMAS_GIFT, BIRTHDAY_GIFT, PRODUCT_GIFT_CHRISTMAS, GIFT_CATEGORY, PRODUCT_GIFT_CHRISTMAS, GIFT_PRODUCTS_REF

logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)
testing = tools.config.get("test_enable")


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
    global_id = fields.Char(
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
        "Sponsored child code", related="child_id.local_id", readonly=True
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
    name = fields.Char(store=True, compute="name_get", copy=False)
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
        readonly=False,
        states={"terminated": [("readonly", True)]},
        ondelete="restrict",
        tracking=True,
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
    is_first_sponsorship = fields.Boolean(readonly=True)
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
        help="Whether gift to the child is possible at the moment or not"
    )
    can_write_letter = fields.Boolean(
        compute="_compute_can_write_letter",
        help="Whether letter to the child is possible at the moment or not"
    )
    is_direct_debit = fields.Boolean(
        compute="_compute_is_direct_debit",
        help="Is paid by direct debit"
    )

    _sql_constraints = [
        (
            "unique_global_id",
            "unique(global_id)",
            "You cannot have same global ids for contracts",
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
        self.contract_line_ids = self._get_sponsorship_standard_lines(self.type in ["SC", "SWP"])

    @api.model
    def _get_sponsorship_standard_lines(self, correspondence):
        """ Select Sponsorship and General Fund by default """
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
                {'pricelist': pricelist.id, 'partner': self.partner_id.id}) \
                ._compute_product_price()
            gen_product.with_context(
                {'pricelist': pricelist.id, 'partner': self.partner_id.id}) \
                ._compute_product_price()

        sponsorship_vals = {
            "product_id": sponsorship_product.id,
            "quantity": 0 if correspondence else 1,
            "amount": 0 if correspondence else sponsorship_product.list_price,
            "subtotal": 0 if correspondence else sponsorship_product.list_price,
        }
        gen_vals = {
            "product_id": gen_product.id,
            "quantity": 0 if correspondence else 1,
            "amount": 0 if correspondence else gen_product.list_price,
            "subtotal": 0 if correspondence else gen_product.list_price,
        }
        res.append((0, 0, sponsorship_vals))
        res.append((0, 0, gen_vals))
        return res

    @api.depends("partner_id", "correspondent_id")
    def _compute_fully_managed(self):
        """Tells if the correspondent and the payer is the same person."""
        for contract in self:
            contract.fully_managed = contract.partner_id == contract.correspondent_id

    def _compute_last_paid_invoice(self):
        """ Override to exclude gift invoices. """
        for contract in self:
            contract.last_paid_invoice_date = max(
                contract.invoice_line_ids.with_context(lang="en_US")
                .filtered(
                    lambda l: l.payment_state == "paid"
                              and l.product_id.categ_name != GIFT_CATEGORY
                )
                .mapped("move_id.invoice_date")
                or [False]
            )

    def _compute_invoices(self):
        gift_contracts = self.filtered(lambda c: c.type == "G")
        for contract in gift_contracts:
            invoices = contract.mapped(
                "contract_line_ids.sponsorship_id.invoice_line_ids.move_id"
            )
            gift_invoices = invoices.filtered(
                lambda i: i.invoice_category == "gift"
                          and i.state not in ("cancel", "draft")
            )
            contract.nb_invoices = len(gift_invoices)
        super(SponsorshipContract, self - gift_contracts)._compute_invoices()

    def _compute_gift_partner(self):
        for contract in self:
            contract.gift_partner_id = getattr(
                contract, contract.send_gifts_to, contract.correspondent_id
            )

    @api.depends(
        "correspondent_id", "correspondent_id.ref", "child_id", "child_id.local_id"
    )
    def name_get(self):
        """ Gives a friendly name for a sponsorship """
        result = []
        for contract in self:
            if contract.correspondent_id.ref or contract.reference:
                name = contract.correspondent_id.ref or contract.reference
                if contract.child_id:
                    name += " - " + contract.child_code
                elif contract.contract_line_ids:
                    name += " - " + contract.contract_line_ids[0].product_id.name
                contract.name = name
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
        days_allowed = self.env["ir.config_parameter"].sudo().get_param(
            "sponsorship_compassion.time_allowed_for_gifts", 90)
        now = fields.Datetime.now()
        for sponsorship in self:
            hold_gifts = sponsorship.project_id.hold_gifts and not \
                self.env.context.get("allow_during_suspension")
            is_allowed = sponsorship.state not in ["terminated", "cancelled", "draft"] and not hold_gifts
            if sponsorship.state == "terminated" and not hold_gifts:
                is_allowed = (now - sponsorship.end_date).days <= int(days_allowed)
            sponsorship.can_make_gift = is_allowed

    def _compute_can_write_letter(self):
        days_allowed = self.env["ir.config_parameter"].sudo().get_param(
            "sponsorship_compassion.time_allowed_for_letters", 90)
        now = fields.Datetime.now()
        for sponsorship in self:
            hold_letters = sponsorship.project_id.hold_s2b_letters and not \
                self.env.context.get("allow_during_suspension")
            is_allowed = sponsorship.state not in ["terminated", "cancelled", "draft"] and not hold_letters
            if sponsorship.state == "terminated" and not hold_letters:
                is_allowed = (now - sponsorship.end_date).days <= int(days_allowed)
            sponsorship.can_write_letter = is_allowed

    def _filter_due_invoices(self):
        # Gifts should not be counted in due invoices
        # Fund-suspended projects are also excluded
        # Correspondence and gift contracts are also excluded
        valid_contracts = self.filtered(lambda s: s.type in ("S", "O") and not s.child_id.project_id.hold_cdsp_funds)
        invoices = super(SponsorshipContract, valid_contracts)._filter_due_invoices()
        return invoices.filtered(lambda i: i.invoice_category != "gift")

    def _compute_is_direct_debit(self):
        dd_modes = self.env['account.payment.mode'].search([('payment_method_code', 'like', '%direct_debit')])
        for contract in self:
            contract.is_direct_debit = contract.payment_mode_id in dd_modes

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    @api.model
    def create(self, vals):
        """ Perform various checks on contract creations
        """
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
        """ Perform various checks on contract modification """
        if "child_id" in vals:
            self._link_unlink_child_to_sponsor(vals)

        old_partners = self.env["res.partner"]
        if "partner_id" in vals:
            old_partners = self.mapped("partner_id")

        updated_correspondents = self.env[self._name]
        previous_states = []
        if "correspondent_id" in vals:
            previous_states.extend([r.state for r in self])
            updated_correspondents = self.filtered("global_id")
            if not self.env.context.get("no_upsert"):
                for record in updated_correspondents:
                    record._remove_correspondent()

            for child in self.mapped("child_id"):
                child.child_sponsored(vals["correspondent_id"])

        # Change the sub_sponsorship_id value in the previous parent_id
        if "parent_id" in vals:
            self.mapped("parent_id").write({"sub_sponsorship_id": False})

        super().write(vals)

        if "reading_language" in vals:
            (self - updated_correspondents)._on_language_changed()

        if "partner_id" in vals:
            self.mapped("partner_id").update_number_sponsorships()
            old_partners.update_number_sponsorships()

        if "correspondent_id" in vals and not self.env.context.get("no_upsert"):
            for record, previous_state in zip(self, previous_states):
                if previous_state not in ["active"]:
                    continue
                success, error_msg = record.add_correspondent()
                if success is False:
                    self.env.user.notify_danger(error_msg)

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
            if "S" in contract.type and contract.state != "draft" and not self.env.context.get("force_delete"):
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
        """ Called when GMC received the commitment. """
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

    def cancel_sent(self, vals):
        """ Called when GMC received the commitment cancel request. """
        self.ensure_one()
        hold_id = vals.get("hold_id")
        hold = self.env["compassion.hold"].search([
            "|", ("hold_id", "=", hold_id), ("id", "=", hold_id)])
        if self.hold_expiration_date and self.hold_expiration_date > fields.Datetime.now():
            hold_expiration = self.hold_expiration_date
            child = self.child_id
            hold.write({
                "child_id": child.id,
                "type": HoldType.SPONSOR_CANCEL_HOLD.value,
                "channel": "sponsor_cancel",
                "expiration_date": hold_expiration,
                "primary_owner": self.write_uid.id,
                "state": "active",
            })
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
        """ On partner change, we set the new commitment number
        (for gift identification). """
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
        """ If a previous sponsorship is selected, the origin should be
        SUB Sponsorship. """
        if self.parent_id:
            self.origin_id = self.parent_id.origin_id.id

    def open_contract(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
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
        """ Hook for doing something when contract is activated.
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
        for contract in self.filtered(lambda c: "S" in c.type):
            gift_contract_lines = con_line_obj.search(
                [("sponsorship_id", "=", contract.id)]
            )
            gift_contracts = gift_contract_lines.mapped("contract_id")
            if gift_contracts:
                gift_contracts.contract_active()

        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        partners.update_number_sponsorships()
        check_duplicate_activity_id = False
        # check_duplicate_activity_id = self.env.ref(
        #     "cms_form_compassion.activity_check_duplicates").id
        if self.mapped("partner_id.activity_ids").filtered(
                lambda l: l.activity_type_id.id == check_duplicate_activity_id) \
                or self.mapped("correspondent_id.activity_ids").filtered(
            lambda l: l.activity_type_id.id == check_duplicate_activity_id):
            raise UserError(
                _("Please verify the partner before validating the sponsorship")
            )
        # Creating the messages to send to GMC when a sponsorship is activated
        for contract in self.filtered(lambda c: "S" in c.type):
            # UpsertConstituent Message
            partner = contract.correspondent_id
            partner.upsert_constituent()
            contract.upsert_sponsorship()
        return True

    def contract_cancelled(self):
        super().contract_cancelled()
        self.filtered(lambda c: "S" in c.type)._on_sponsorship_finished()
        return True

    def contract_terminated(self):
        super().contract_terminated()
        self.filtered(lambda c: "S" in c.type)._on_sponsorship_finished()
        return True

    def contract_waiting(self):
        contracts = self.filtered(lambda c: c.type == "O")
        if contracts:
            super(SponsorshipContract, contracts).contract_waiting()
        for contract in self - contracts:
            if not contract.start_date:
                contract.start_date = fields.Datetime.now()
            old_sponsorships = contract.correspondent_id.sponsorship_ids.filtered(
                lambda c: c.state != "cancelled" and c.start_date
                          and c.start_date < contract.start_date)
            contract.is_first_sponsorship = not old_sponsorships

            if contract.type == "G":
                # Activate directly if sponsorship is already active
                for line in contract.contract_line_ids:
                    sponsorship = line.sponsorship_id
                    if sponsorship.state == "active":
                        contract.contract_active()
            elif contract.type == "S" or (contract.type in ["SC", "SWP"] and contract.total_amount > 0):
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
        """ Set back a cancelled contract to draft state. """
        super().action_cancel_draft()
        for contract in self.filtered("child_id"):
            if contract.child_id.is_available:
                contract.child_id.child_sponsored(contract.correspondent_id.id)
            else:
                contract.child_id = False
        return True

    def upsert_sponsorship(self):
        """ Creates and returns upsert messages for sponsorships. """
        messages = self.env["gmc.message"]
        action = self.env.ref("sponsorship_compassion.create_sponsorship")
        if self.env.context.get("no_upsert"):
            return messages
        for sponsorship in self:
            messages += messages.create({
                "action_id": action.id,
                "child_id": sponsorship.child_id.id,
                "partner_id": sponsorship.correspondent_id.id,
                "object_id": sponsorship.id,
            })
        return messages

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.constrains('birthday_invoice', 'christmas_invoice')
    def _check_gift_invoice_method(self):
        for contract in self:
            if contract.birthday_invoice or contract.christmas_invoice:
                if not contract.is_direct_debit:
                    raise UserError("You can't have an amount for 'Birthday Invoice' "
                                    "or 'Christmas Invoice' if the payment mode isn't a direct debit.")

    def _on_language_changed(self):
        """ Update the preferred language in GMC. """
        messages = self.upsert_sponsorship().with_context({"async_mode": False})
        error_msg = "Error when updating sponsorship language. You may be out of sync with GMC - please try again."
        for message in messages:
            try:
                message.process_messages()
                if "failure" in message.state:
                    failure = message.failure_reason or error_msg
                    self.env.user.notify_danger(failure, "Language update failed.")
            except:
                self.env.user.notify_danger(error_msg, "Language update failed.")
                logger.error(error_msg, exc_info=True)

    def _remove_correspondent(self):
        self.ensure_one()
        message_obj = self.env["gmc.message"].with_context({"async_mode": False})
        cancel_action = self.env.ref("sponsorship_compassion.cancel_sponsorship")

        if self.state in ("cancelled", "terminated"):
            raise UserError(_("You can't change the correspondent of a"
                              " cancelled or terminated sponsorship"))

        hold_expiration_date = self.env["compassion.hold"].get_default_hold_expiration(
            HoldType.SPONSOR_CANCEL_HOLD)
        self.hold_expiration_date = hold_expiration_date

        # Cancel sponsorship at GMC
        message = message_obj.create(
            {
                "action_id": cancel_action.id,
                "child_id": self.child_id.id,
                "partner_id": self.correspondent_id.id,
                "object_id": self.id,
            }
        )
        message.process_messages()

        answer = json.loads(message.answer)
        if not isinstance(answer, dict) or "Code" not in answer:
            raise UserError(_("Invalid GMC answer"))
        if message.state == "failure":
            error_message = answer["Message"]
            logger.error(message.failure_reason)
            raise UserError(_("GMC returned an error :") + "\n" + error_message)
        elif message.state == "odoo_failure":
            logger.warning(message.failure_reason)

        self.global_id = False
        self.state = "terminated"
        self.correspondent_id.update_number_sponsorships()
        return True

    def add_correspondent(self):
        self.ensure_one()
        self.correspondent_id.upsert_constituent().process_messages()

        # Create new sponsorships at GMC
        message = self.upsert_sponsorship()
        message.with_context({'async_mode': False}).process_messages()

        answer = json.loads(message.answer)
        if not isinstance(answer, dict) or "Message" not in answer:
            return False, _("Invalid GMC answer")
        if "failure" in message.state:
            error_message = answer["Message"]
            logger.error(error_message)
            return False, _("Couldn't activate the new correspondent, GMC returned "
                            "the following error: ") + "\n" + error_message

        self.correspondent_id.update_number_sponsorships()
        return True, ""

    def _on_sponsorship_finished(self):
        """ Called when a sponsorship is terminated or cancelled:
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
                    contract.contract_terminated()

            if sponsorship.global_id and sponsorship.end_reason_id != departure:
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
            elif not sponsorship.global_id:
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
        """Link/unlink child to sponsor
        """
        child_id = vals.get("child_id")
        for contract in self:
            if (
                    "S" in contract.type
                    and contract.child_id
                    and contract.child_id.id != child_id
            ):
                # Free the previously selected child
                contract.child_id.child_unsponsored()
            if child_id and "S" in contract.type:
                # Mark the selected child as sponsored
                self.env["compassion.child"].browse(child_id).child_sponsored(
                    vals.get("correspondent_id") or contract.correspondent_id.id
                )

    def _generate_invoices(self):
        invoicer = super()._generate_invoices()
        # We don't generate gift if the contract isn't active
        contracts = self.filtered(lambda c: c.state == 'active')
        contracts._generate_gifts(invoicer, BIRTHDAY_GIFT)
        contracts._generate_gifts(invoicer, CHRISTMAS_GIFT)
        return invoicer

    def _generate_gifts(self, invoicer, gift_type):
        """ Creates the annual gifts for sponsorships that
        have set the option for automatic birthday or christmas gifts creation. """
        logger.debug(f"Automatic {gift_type} Gift Generation Started.")
        invoice_err_gen = False
        # Search active Sponsorships with automatic birthday gift
        contracts = self

        product_id = (
            self.env["product.product"]
            .search(
                [("default_code", "=", GIFT_PRODUCTS_REF[0] if gift_type == BIRTHDAY_GIFT else PRODUCT_GIFT_CHRISTMAS)],
                limit=1)
            .id
        )

        # Don't generate gift for contract that are holding gifts or if they don't have an amount for the gift
        for contract in contracts:
            if contract.project_id.hold_gifts \
                    or eval(f"contract.{gift_type}_invoice") <= 0:
                contracts -= contract

        if contracts:
            total = str(len(contracts))
            count = 1
            logger.debug(f"Found {total} {gift_type} Gifts to generate.")

            gift_wizard = (
                self.env["generate.gift.wizard"]
                .with_context(recurring_invoicer_id=invoicer.id)
                .create(
                    {
                        "description": f"Automatic {gift_type} gift",
                        "invoice_date": datetime.today().date(),
                        "product_id": product_id,
                        "amount": 0.0,
                    }
                )
            )

            # Generate invoices
            for contract in contracts:
                logger.debug(f"{gift_type} Gift Generation: {count}/{total} ")
                try:
                    self._generate_gift(gift_wizard, contract, invoicer, gift_type)
                except Exception as e:
                    logger.error(f"Gift generation failed. {e}")
                    invoice_err_gen = True
                finally:
                    count += 1

        logger.debug(f"Automatic {gift_type} Gift Generation Finished !!")
        return invoicer.with_context(invoice_err_gen=invoice_err_gen)

    def _generate_gift(self, gift_wizard, contract, invoicer, gift_type):
        gift_wizard.write(
            {"amount": eval(f"contract.{gift_type}_invoice")}
        )
        gift_wizard.with_context(active_ids=contract.id, invoicer=invoicer).generate_invoice()

    def invoice_paid(self, invoice):
        """ Prevent to reconcile invoices for sponsorships older than 3 months. """
        bypass_state = self.env.context.get("bypass_state", False)
        for invl in invoice.invoice_line_ids:
            if invl.contract_id and invl.contract_id.child_id:
                contract = invl.contract_id

                # Check contract is active or terminated recently.
                if contract.state == "cancelled" and not bypass_state:
                    raise UserError(f"The contract {contract.name} is not active.")
                if contract.state == "terminated" and contract.end_date and not bypass_state:
                    limit = datetime.now() - relativedelta(days=180)
                    ended_since = contract.end_date
                    if ended_since < limit:
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
                        len(contract.invoice_line_ids.filtered(
                            lambda i: i.payment_state == "paid"))
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
        """ Hook for holding gifts. """
        pass

    def reactivate_gifts(self):
        """ Hook for reactivating gifts. """
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
