##############################################################################
#
#    Copyright (C) 2014-2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import os
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.queue_job.job import job, related_action

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from .product_names import GIFT_CATEGORY, SPONSORSHIP_CATEGORY

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
        track_visibility="onchange",
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
        track_visibility="onchange",
    )
    reading_language = fields.Many2one(
        "res.lang.compassion",
        "Preferred language",
        track_visiblity="onchange",
        readonly=False,
    )
    transfer_partner_id = fields.Many2one(
        "compassion.global.partner", "Transferred to", readonly=False
    )
    global_id = fields.Char(
        help="Connect global ID", readonly=True, copy=False, track_visibility="onchange"
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
    suspended_amount = fields.Float(compute="_compute_suspended_amount")

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
        track_visibility="onchange",
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
    commitment_number = fields.Integer(
        "Partner Contract Number", required=True, copy=False,
    )
    months_paid = fields.Integer(compute="_compute_months_paid")
    origin_id = fields.Many2one(
        "recurring.contract.origin",
        "Origin",
        ondelete="restrict",
        track_visibility="onchange",
        index=True,
        readonly=False,
    )
    parent_id = fields.Many2one(
        "recurring.contract",
        "Previous sponsorship",
        track_visibility="onchange",
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
        track_visibility="onchange",
    )
    type = fields.Selection(
        [
            ("O", "General"),
            ("G", "Child Gift"),
            ("S", "Sponsorship"),
            ("SC", "Correspondence"),
        ],
        required=True,
        default="O",
    )
    group_freq = fields.Char(
        string="Payment frequency", compute="_compute_frequency", readonly=True
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

    @api.onchange("type")
    def _create_empty_lines_for_correspondence(self):
        self.contract_line_ids = self._get_sponsorship_standard_lines(self.type == "SC")

    @api.model
    def _get_sponsorship_standard_lines(self, correspondence):
        """ Select Sponsorship and General Fund by default """
        res = [(5, 0, 0)]
        sponsorship_product = self.env["product.template"].search(
            [
                ("default_code", "=", "sponsorship"),
                ("company_id", "=", self.env.user.company_id.id),
            ]
        )
        gen_product = self.env["product.template"].search(
            [
                ("default_code", "=", "fund_gen"),
                ("company_id", "=", self.env.user.company_id.id),
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

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """ Display only contract type needed in view.
        """
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        if view_type == "form" and "type" in res["fields"]:
            s_type = self._context.get("default_type", "O")
            if "S" in s_type:
                # Remove non sponsorship types
                res["fields"]["type"]["selection"].pop(0)
                res["fields"]["type"]["selection"].pop(0)
            else:
                # Remove type Sponsorships so that we cannot change to it.
                res["fields"]["type"]["selection"].pop(2)
                res["fields"]["type"]["selection"].pop(2)

        return res

    @api.multi
    @api.depends("partner_id", "correspondent_id")
    def _compute_fully_managed(self):
        """Tells if the correspondent and the payer is the same person."""
        for contract in self:
            contract.fully_managed = contract.partner_id == contract.correspondent_id

    @api.multi
    def _compute_last_paid_invoice(self):
        """ Override to exclude gift invoices. """
        for contract in self:
            contract.last_paid_invoice_date = max(
                contract.invoice_line_ids.with_context(lang="en_US")
                .filtered(
                    lambda l: l.state == "paid"
                    and l.product_id.categ_name != GIFT_CATEGORY
                )
                .mapped("invoice_id.date_invoice")
                or [False]
            )

    @api.multi
    def _compute_invoices(self):
        gift_contracts = self.filtered(lambda c: c.type == "G")
        for contract in gift_contracts:
            invoices = contract.mapped(
                "contract_line_ids.sponsorship_id.invoice_line_ids.invoice_id"
            )
            gift_invoices = invoices.filtered(
                lambda i: i.invoice_type == "gift"
                and i.state not in ("cancel", "draft")
            )
            contract.nb_invoices = len(gift_invoices)
        super(SponsorshipContract, self - gift_contracts)._compute_invoices()

    @api.multi
    def _compute_gift_partner(self):
        for contract in self:
            contract.gift_partner_id = getattr(
                contract, contract.send_gifts_to, contract.correspondent_id
            )

    @api.multi
    def _compute_suspended_amount(self):
        """ Suspended amount is all amount donated to suspension product
        and amount not reconciled. """
        suspend_config = int(
            self.env["ir.config_parameter"]
                .sudo()
                .get_param("sponsorship_compassion.suspend_product_id", 0)
        )
        suspend_product = self.env["product.product"].browse(suspend_config).exists()
        for contract in self.filtered("child_id"):
            amount = 0
            if suspend_product:
                amount += sum(
                    self.env["account.invoice.line"]
                    .search(
                        [
                            ("contract_id", "=", contract.id),
                            ("state", "=", "paid"),
                            ("product_id", "=", suspend_product.id),
                        ]
                    )
                    .mapped("price_subtotal")
                    or [0]
                )
            amount += contract.partner_id.debit
            contract.suspended_amount = amount

    @api.multi
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

    @api.multi
    @api.depends("activation_date", "state")
    def _compute_active(self):
        for contract in self:
            contract.is_active = bool(
                contract.activation_date
            ) and contract.state not in ("terminated", "cancelled")

    @api.multi
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

    @api.multi
    def _compute_months_paid(self):
        """This is a query returning the number of months paid for a
        sponsorship."""
        self._cr.execute(
            "SELECT c.id as contract_id, "
            "12 * (EXTRACT(year FROM next_invoice_date) - "
            "      EXTRACT(year FROM current_date))"
            " + EXTRACT(month FROM c.next_invoice_date) - 1"
            " - COALESCE(due.total, 0) as paidmonth "
            "FROM recurring_contract c left join ("
            # Open invoices to find how many months are due
            "   select contract_id, count(distinct invoice_id) as total "
            "   from account_invoice_line l join product_product p on "
            "       l.product_id = p.id "
            "   where state='open' and "
            # Exclude gifts from count
            "   categ_name != 'Sponsor gifts'"
            "   group by contract_id"
            ") due on due.contract_id = c.id "
            "WHERE c.id = ANY (%s)",
            [self.ids],
        )
        res = self._cr.dictfetchall()
        dict_contract_id_paidmonth = {
            row["contract_id"]: int(row["paidmonth"] or 0) for row in res
        }
        for contract in self:
            contract.months_paid = dict_contract_id_paidmonth.get(contract.id)

    @api.multi
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

    @api.multi
    def write(self, vals):
        """ Perform various checks on contract modification """
        if "child_id" in vals:
            self._link_unlink_child_to_sponsor(vals)

        if "partner_id" in vals:
            old_partners = self.mapped("partner_id")

        updated_correspondents = self.env[self._name]
        if "correspondent_id" in vals:
            old_correspondents = self.mapped("correspondent_id")
            updated_correspondents = self._on_change_correspondant(
                vals["correspondent_id"]
            )
            for child in self.mapped("child_id"):
                child.child_sponsored(vals["correspondent_id"])

        # Change the sub_sponsorship_id value in the previous parent_id
        if "parent_id" in vals:
            self.mapped("parent_id").write({"sub_sponsorship_id": False})

        super().write(vals)

        try:
            if not testing:
                self.env.cr.commit()
            if updated_correspondents:
                updated_correspondents._on_correspondant_changed()
        except:
            # TODO CO-3293 create activity to warn someone
            logger.error(
                "Error while changing correspondant at GMC. "
                "The sponsorship is no longer active at GMC side. "
                "Please activate it again manually.",
                exc_info=True,
            )

        if "reading_language" in vals:
            (self - updated_correspondents)._on_language_changed()

        if "partner_id" in vals:
            # Move invoices to new partner
            invoices = self.invoice_line_ids.mapped("invoice_id").filtered(
                lambda i: i.state in ("open", "draft")
            )
            invoices.action_invoice_cancel()
            invoices.action_invoice_draft()
            invoices.write({"partner_id": vals["partner_id"]})
            invoices.action_invoice_open()
            # Update number of sponsorships
            self.mapped("partner_id").update_number_sponsorships()
            old_partners.update_number_sponsorships()

        if "correspondent_id" in vals:
            self.mapped("correspondent_id").update_number_sponsorships()
            old_correspondents.update_number_sponsorships()

        # Set the sub_sponsorship_id in the current parent_id
        if "parent_id" in vals:
            for sponsorship in self.filtered("parent_id"):
                parent = sponsorship.parent_id
                parent.sub_sponsorship_id = sponsorship
                sponsorship.sponsorship_line_id = parent.sponsorship_line_id

        if "group_id" in vals or "partner_id" in vals:
            self._on_group_id_changed()

        return True

    @api.multi
    def unlink(self):
        for contract in self:
            # We can only delete draft sponsorships.
            if "S" in contract.type and contract.state != "draft":
                raise UserError(_("You cannot delete a validated sponsorship."))
            # Remove sponsor of child and release it
            if "S" in contract.type and contract.child_id:
                if contract.child_id.sponsor_id == contract.correspondent_id:
                    child = contract.child_id.with_context({})
                    child.child_unsponsored()
                    child.child_released()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def _on_invoice_line_removal(self, invl_rm_data):
        pass

    @api.multi
    def suspend_contract(self):
        """
        If ir.config.parameter is set : change sponsorship invoices with
        a fund donation set in the config.
        Otherwise, Cancel the number of invoices specified starting
        from a given date. This is useful to suspend a contract for a given
        period."""
        date_start = date.today()

        config_obj = self.env["ir.config_parameter"].sudo()
        suspend_config = config_obj.get_param(
            "sponsorship_compassion.suspend_product_id"
        )
        # Cancel invoices in the period of suspension
        self._clean_invoices(date_start, keep_lines=_("Center suspended"))

        for contract in self:
            # Add a note in the contract and in the partner.
            project_code = contract.project_id.fcp_id
            contract.message_post(
                body=_(
                    "The project %s was suspended and funds are retained."
                    "<br/>Invoices due in the suspension period "
                    "are automatically cancelled."
                ) % project_code,
                subject=_("Project Suspended"),
                message_type="comment",
            )
            contract.partner_id.message_post(
                body=_(
                    "The project %s was suspended and"
                    " funds are retained for child %s. <b>"
                    "<br/>Invoices due in the suspension period "
                    "are automatically cancelled."
                ) % (project_code, contract.child_code),
                subject=_("Project Suspended"),
                message_type="comment",
            )

        # Change invoices if config tells to do so.
        if suspend_config:
            product_id = int(suspend_config)
            self._suspend_change_invoices(date_start, product_id)

        return True

    @api.multi
    def _suspend_change_invoices(self, since_date, product_id):
        """ Change cancelled sponsorship invoices and put them for given
        product. Re-open invoices. """
        cancel_inv_lines = (
            self.env["account.invoice.line"]
                .with_context(lang="en_US")
                .search(
                [
                    ("contract_id", "in", self.ids),
                    ("state", "=", "cancel"),
                    ("product_id.categ_name", "=", SPONSORSHIP_CATEGORY),
                    ("due_date", ">=", since_date),
                ]
            )
        )
        invoices = cancel_inv_lines.mapped("invoice_id")
        invoices.action_invoice_draft()
        invoices.env.clear()
        vals = self.get_suspend_invl_data(product_id)
        cancel_inv_lines.write(vals)
        invoices.action_invoice_open()

    @api.multi
    def get_suspend_invl_data(self, product_id):
        """ Returns invoice_line data for a given product when center
        is suspended. """

        product = self.env["product.product"].browse(product_id)
        vals = {
            "product_id": product_id,
            "account_id": product.property_account_income_id.id,
            "name": "Replacement of sponsorship (fund-suspended)",
        }
        rec = self.env["account.analytic.default"].account_get(product.id)
        if rec and rec.analytic_id:
            vals["account_analytic_id"] = rec.analytic_id.id

        return vals

    @api.multi
    def reactivate_contract(self):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        date_start = date.today()
        config_obj = self.env["ir.config_parameter"]
        suspend_config = config_obj.get_param(
            "sponsorship_compassion.suspend_product_id"
        )
        invl_obj = self.env["account.invoice.line"]
        sponsorship_product = self.env["product.product"].search(
            [("default_code", "=", "sponsorship")]
        )
        if suspend_config:
            # Revert future invoices with sponsorship product
            susp_product_id = int(suspend_config)
            invl_lines = invl_obj.search(
                [
                    ("contract_id", "in", self.ids),
                    ("product_id", "=", susp_product_id),
                    ("state", "in", ["open", "paid"]),
                    ("due_date", ">=", date_start),
                ]
            )
            invl_data = {
                "product_id": sponsorship_product.id,
                "account_id": sponsorship_product.property_account_income_id.id,
                "name": sponsorship_product.name,
            }
            rec = self.env["account.analytic.default"].account_get(
                sponsorship_product.id
            )
            if rec and rec.analytic_id:
                invl_data["account_analytic_id"] = rec.analytic_id.id
            invl_lines.write(invl_data)

            invoices = invl_lines.mapped("invoice_id")
            contracts = invl_lines.mapped("contract_id")
            reconciles = invoices.filtered(lambda inv: inv.state == "paid").mapped(
                "payment_move_line_ids.full_reconcile_id"
            )

            # Unreconcile paid invoices
            reconciles.mapped("reconciled_line_ids").remove_move_reconcile()
            # Cancel and confirm again invoices to update move lines
            invoices.action_invoice_cancel()
            invoices.action_invoice_draft()
            invoices.env.clear()
            invoices.action_invoice_open()
        else:
            # Open again cancelled invoices
            inv_lines = invl_obj.search(
                [
                    ("contract_id", "in", self.ids),
                    ("product_id", "=", sponsorship_product.id),
                    ("state", "=", "cancel"),
                    ("due_date", ">=", date_start),
                ]
            )
            contracts = inv_lines.mapped("contract_id")
            to_open = inv_lines.mapped("invoice_id").filtered(
                lambda inv: inv.state == "cancel"
            )
            to_open.action_invoice_draft()
            to_open.env.clear()
            for i in to_open:
                i.action_invoice_open()

        # Log a note in the contracts
        for contract in contracts:
            contract.message_post(
                body=_(
                    "The project was reactivated."
                    "<br/>Invoices due in the suspension period "
                    "are automatically reverted."
                ),
                subject=_("Project Reactivated"),
                type="comment",
            )

    def commitment_sent(self, vals):
        """ Called when GMC received the commitment. """
        self.ensure_one()
        # We don't need to write back partner and child
        vals.pop("child_id", False)
        vals.pop("correspondent_id", False)
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
        if self.hold_expiration_date:
            hold_expiration = self.hold_expiration_date
            if "hold_id" in vals and hold_expiration >= datetime.now():
                child = self.child_id
                hold_vals = {
                    "hold_id": vals["hold_id"],
                    "child_id": child.id,
                    "type": HoldType.SPONSOR_CANCEL_HOLD.value,
                    "channel": "sponsor_cancel",
                    "expiration_date": self.hold_expiration_date,
                    "primary_owner": self.write_uid.id,
                    "state": "active",
                }
                hold = self.env["compassion.hold"].create(hold_vals)
                child.child_consigned(hold.id)
        return True

    @api.multi
    def get_inv_lines_data(self):
        """ Contract gifts relate their invoice lines to sponsorship,
            Correspondence sponsorships don't create invoice lines.
            Add analytic account to invoice_lines.
        """
        contracts = self.filtered(lambda c: c.total_amount != 0)
        suspend_config = int(
            self.env["ir.config_parameter"]
                .sudo()
                .get_param("sponsorship_compassion.suspend_product_id", 0)
        )
        res = list()
        for contract in contracts:
            invl_datas = super(SponsorshipContract, contract).get_inv_lines_data()

            # If project is suspended, either skip invoice or replace product
            if contract.type in ["S", "SC"] and contract.project_id.hold_cdsp_funds:
                if not suspend_config:
                    continue
                for invl_data in invl_datas:
                    current_product = (
                        self.env["product.product"]
                            .with_context(lang="en_US")
                            .browse(invl_data["product_id"])
                    )
                    if current_product.categ_name == SPONSORSHIP_CATEGORY:
                        invl_data.update(self.get_suspend_invl_data(suspend_config))

            if contract.type == "G":
                for i in range(0, len(invl_datas)):
                    sponsorship = contract.contract_line_ids[i].sponsorship_id
                    gen_states = sponsorship.group_id._get_gen_states()
                    if (
                            sponsorship.state in gen_states
                            and not sponsorship.project_id.hold_gifts
                    ):
                        invl_datas[i]["contract_id"] = sponsorship.id
                    else:
                        logger.error(
                            f"No active sponsorship found for "
                            f"child {sponsorship.child_code}. "
                            f"The gift contract with "
                            f"id {contract.id} is not valid."
                        )
                        continue

            # Find the analytic account
            for invl_data in invl_datas:
                contract = self.env["recurring.contract"].browse(
                    invl_data["contract_id"]
                )
                product_id = invl_data["product_id"]
                partner_id = contract.partner_id.id
                analytic = contract.origin_id.analytic_id
                if not analytic:
                    a_default = self.env["account.analytic.default"].account_get(
                        product_id, partner_id, date=fields.Date.today()
                    )
                    analytic = a_default and a_default.analytic_id
                if analytic:
                    invl_data.update({"account_analytic_id": analytic.id})
                    a_default = self.env["account.analytic.default"].account_get(
                        product_id, partner_id, date=fields.Date.today()
                    )

                tags = a_default and a_default.analytic_tag_ids
                if tags:
                    invl_data.update({"analytic_tag_ids": [(6, 0, tags.ids)]})

            # Append the invoice lines.
            res.extend(invl_datas)

        return res

    @api.multi
    @job(default_channel="root.sponsorship_compassion")
    @related_action(action="related_action_contract")
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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange("partner_id", "correspondent_id")
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
        if self.partner_id and not self.correspondent_id:
            self.correspondent_id = self.partner_id

    @api.multi
    def open_invoices(self):
        res = super().open_invoices()
        if self.type == "G":
            # Include gifts of related sponsorship for gift contracts
            sponsorship_invoices = self.mapped(
                "contract_line_ids.sponsorship_id.invoice_line_ids.invoice_id"
            )
            gift_invoices = sponsorship_invoices.filtered(
                lambda i: i.invoice_type == "gift"
            )
            res["domain"] = [("id", "in", gift_invoices.ids)]
        return res

    @api.onchange("parent_id")
    def on_change_parent_id(self):
        """ If a previous sponsorship is selected, the origin should be
        SUB Sponsorship. """
        if self.parent_id:
            self.origin_id = self.parent_id.origin_id.id

    @api.multi
    def open_contract(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contract",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "current",
            "context": self.with_context(default_type=self.type).env.context,
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Hook for doing something when contract is activated.
        Update child to mark it has been sponsored,
        and activate gift contracts.
        Send messages to GMC.
        """
        for contract in self.filtered(lambda c: "S" in c.type):
            # UpsertConstituent Message
            partner = contract.correspondent_id
            partner.upsert_constituent()

            message_obj = self.env["gmc.message"]
            action_id = self.env.ref("sponsorship_compassion.create_sponsorship").id

            message_vals = {
                "partner_id": contract.correspondent_id.id,
                "child_id": contract.child_id.id,
                "action_id": action_id,
                "object_id": contract.id,
            }
            message_obj.create(message_vals)

        self.filtered(lambda c: not c.is_active).write(
            {"activation_date": fields.Datetime.now()}
        )
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
            gift_contract_lines.mapped("contract_id").contract_active()

        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        partners.update_number_sponsorships()
        return True

    @api.multi
    def contract_cancelled(self):
        super().contract_cancelled()
        self.filtered(lambda c: "S" in c.type)._on_sponsorship_finished()
        return True

    @api.multi
    def contract_terminated(self):
        super().contract_terminated()
        self.filtered(lambda c: "S" in c.type)._on_sponsorship_finished()
        return True

    @api.multi
    def contract_waiting(self):
        contracts = self.filtered(lambda c: c.type == "O")
        if contracts:
            super(SponsorshipContract, contracts).contract_waiting()
        for contract in self - contracts:
            if contract.type == "G":
                # Activate directly if sponsorship is already active
                for line in contract.contract_line_ids:
                    sponsorship = line.sponsorship_id
                    if sponsorship.state == "active":
                        contract.contract_active()
                contract.group_id.generate_invoices()
            if contract.type == "S":
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
                contract.write(
                    {"state": "waiting", "start_date": fields.Datetime.now()}
                )
                contract.group_id.generate_invoices()
            if contract.type == "SC":
                # Activate directly correspondence sponsorships
                contract.contract_active()
        return True

    @api.multi
    def action_cancel_draft(self):
        """ Set back a cancelled contract to draft state. """
        super().action_cancel_draft()
        for contract in self.filtered("child_id"):
            if contract.child_id.is_available:
                contract.child_id.child_sponsored(contract.correspondent_id.id)
            else:
                contract.child_id = False
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_language_changed(self):
        """ Update the preferred language in GMC. """
        action = self.env.ref("sponsorship_compassion.create_sponsorship")
        message_obj = self.env["gmc.message"].with_context(async_mode=False)
        for sponsorship in self.filtered(
                lambda s: s.global_id and s.state not in ("cancelled", "terminated")
        ):
            # Commit at each message processed
            try:
                with self.env.cr.savepoint():
                    message = message_obj.create(
                        {
                            "action_id": action.id,
                            "child_id": sponsorship.child_id.id,
                            "partner_id": sponsorship.correspondent_id.id,
                            "object_id": sponsorship.id,
                        }
                    )
                    message.process_messages()
                    if message.state == "failure":
                        failure = message.failure_reason
                        sponsorship.message_post(failure, _("Language update failed."))
            except:
                logger.error(
                    "Error when updating sponsorship language. "
                    "You may be out of sync with GMC - please try again.",
                    exc_info=True,
                )

    @api.multi
    def _on_change_correspondant(self, correspondent_id):
        """
        This is useful for not having to internally cancel and create
        a new commitment just to change the corresponding partner.
        It will however cancel the commitment at GMC side and create a new
        one.
        But in Odoo, we will not see the commitment has changed.
        """
        message_obj = self.env["gmc.message"].with_context(async_mode=False)
        cancel_action = self.env.ref("sponsorship_compassion.cancel_sponsorship")

        sponsorships = self.filtered(
            lambda s: s.correspondent_id.id != correspondent_id
            and s.global_id
            and s.state not in ("cancelled", "terminated")
        )
        sponsorships.write(
            {
                "hold_expiration_date": self.env[
                    "compassion.hold"
                ].get_default_hold_expiration(HoldType.SPONSOR_CANCEL_HOLD)
            }
        )
        cancelled_sponsorships = self.env[self._name]
        errors = self.env[self._name]

        # Cancel sponsorship at GMC
        messages = message_obj
        for sponsorship in sponsorships:
            messages += message_obj.create(
                {
                    "action_id": cancel_action.id,
                    "child_id": sponsorship.child_id.id,
                    "partner_id": sponsorship.correspondent_id.id,
                    "object_id": sponsorship.id,
                }
            )
        messages.process_messages()
        for i in range(0, len(messages)):
            if messages[i].state == "success":
                cancelled_sponsorships += sponsorships[i]
            else:
                messages[i].unlink()
                errors += sponsorships[i]
        if errors:
            logger.error(
                "Could not cancel contracts with following global_id(s):"
                ", ".join(errors.mapped("global_id"))
            )

            raise RuntimeError(
                _("The current commitment at GMC side could not be " "cancelled.")
            )

        cancelled_sponsorships.write({"global_id": False})
        return cancelled_sponsorships

    @api.multi
    def _on_correspondant_changed(self):
        """
        This is useful for not having to internally cancel and create
        a new commitment just to change the corresponding partner.
        It will however cancel the commitment at GMC side and create a new
        one.
        But in Odoo, we will not see the commitment has changed.
        """
        message_obj = self.env["gmc.message"].with_context(async_mode=False)
        create_action = self.env.ref("sponsorship_compassion.create_sponsorship")

        # Upsert correspondents
        self.mapped("correspondent_id").upsert_constituent().process_messages()

        # Create new sponsorships at GMC
        messages = message_obj
        for sponsorship in self:
            partner = sponsorship.correspondent_id
            messages += message_obj.create(
                {
                    "action_id": create_action.id,
                    "child_id": sponsorship.child_id.id,
                    "partner_id": partner.id,
                    "object_id": sponsorship.id,
                }
            )
        messages.process_messages()
        for i in range(0, len(messages)):
            if not messages[i].state == "success":
                self[i].message_post(
                    body=messages[i].failure_reason,
                    subject=_("The sponsorship is no more active!")
                )

    @api.multi
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
                        ("state", "in", ["new", "failure"]),
                        ("object_id", "=", sponsorship.id),
                    ]
                ).unlink()
                sponsorship.state = "cancelled"
        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        partners.update_number_sponsorships()

    @api.multi
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
            if "S" in contract.type:
                # Mark the selected child as sponsored
                self.env["compassion.child"].browse(child_id).child_sponsored(
                    vals.get("correspondent_id") or contract.correspondent_id.id
                )

    @api.multi
    def invoice_paid(self, invoice):
        """ Prevent to reconcile invoices for fund-suspended projects
            or sponsorships older than 3 months. """
        for invl in invoice.invoice_line_ids:
            if invl.contract_id and invl.contract_id.child_id:
                contract = invl.contract_id

                # Check contract is active or terminated recently.
                if contract.state == "cancelled":
                    raise UserError(f"The contract {contract.name} is not active.")
                if contract.state == "terminated" and contract.end_date:
                    limit = datetime.now() - relativedelta(days=180)
                    ended_since = contract.end_date
                    if ended_since < limit:
                        raise UserError(f"The contract {contract.name} is not active.")

                # Check if project allows this kind of payment.
                payment_allowed = True
                project = contract.project_id
                if invl.product_id.categ_name == SPONSORSHIP_CATEGORY:
                    payment_allowed = (
                        not project.hold_cdsp_funds
                        or (
                            invl.due_date
                            < project.lifecycle_ids[:1].suspension_start_date
                            if project.lifecycle_ids[:1].suspension_start_date
                            else True
                        )
                    )
                if not payment_allowed:
                    raise UserError(
                        f"The project {project.fcp_id} is fund-suspended. "
                        f"You cannot reconcile invoice ({invoice.id})."
                    )

                # Activate gift related contracts (if any)
                if "S" in contract.type:
                    gift_contract_lines = self.env["recurring.contract.line"].search(
                        [
                            ("sponsorship_id", "=", contract.id),
                            ("contract_id.state", "=", "waiting"),
                        ]
                    )
                    gift_contract_lines.mapped("contract_id").contract_active()

                if (
                        len(contract.invoice_line_ids.filtered(
                            lambda i: i.state == "paid"))
                        == 1
                ):
                    contract.partner_id.set_privacy_statement(origin="first_payment")

        # Super method will activate waiting contracts
        # Only activate sponsorships with sponsorship invoice
        to_activate = self
        if invoice.invoice_type != "sponsorship":
            to_activate -= self.filtered(lambda s: "S" in s.type)
        super(SponsorshipContract, to_activate).invoice_paid(invoice)

    @api.multi
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

    @api.multi
    def update_next_invoice_date(self):
        """ Override to force recurring_value to 1
            if contract is a sponsorship, and to bypass ORM for performance.
        """
        for contract in self:
            if "S" in contract.type:
                next_date = contract.next_invoice_date
                next_date += relativedelta(months=+1)
            else:
                next_date = contract._compute_next_invoice_date()
            contract.next_invoice_date = next_date
        return True

    @api.multi
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

    @api.multi
    def _filter_clean_invoices(self, since_date, to_date):
        """ Exclude gifts from clean invoice method. """
        invl_search = super()._filter_clean_invoices(since_date, to_date)
        invl_search.append(("product_id.categ_name", "!=", GIFT_CATEGORY))
        return invl_search

    @job(default_channel="root.recurring_invoicer")
    @related_action(action="related_action_contract")
    def cancel_old_invoices(self):
        """Cancel the old open invoices of a contract
           which are older than the first paid invoice of contract.
           If the invoice has only one contract -> cancel
           Else -> draft to modify the invoice and validate
        """
        invoice_line_obj = self.env["account.invoice.line"]
        paid_invl = invoice_line_obj.search(
            [("contract_id", "in", self.ids), ("state", "=", "paid")],
            order="due_date asc",
            limit=1,
        )
        invoice_lines = invoice_line_obj.search(
            [
                ("contract_id", "in", self.ids),
                ("state", "=", "open"),
                ("due_date", "<", paid_invl.due_date),
            ]
        )

        invoices = invoice_lines.mapped("invoice_id")

        for invoice in invoices:
            invoice_lines = invoice.invoice_line_ids

            inv_lines = self._get_filtered_invoice_lines(invoice_lines)

            if len(inv_lines) == len(invoice_lines):
                invoice.action_invoice_cancel()
            else:
                invoice.action_invoice_cancel()
                invoice.action_invoice_draft()
                invoice.env.clear()
                inv_lines.unlink()
                invoice.action_invoice_open()

    @api.multi
    def _reset_open_invoices_job(self):
        """Clean the open invoices in order to generate new invoices.
        This can be useful if contract was updated when active."""
        invoices_canceled = self._clean_invoices(clean_invoices_paid=False)
        if invoices_canceled:
            invoice_obj = self.env["account.invoice"]
            inv_update_ids = set()
            for contract in self:
                # If some invoices are left cancelled, we update them
                # with new contract information and validate them
                cancel_invoices = invoice_obj.search(
                    [("state", "=", "cancel"), ("id", "in", invoices_canceled.ids)]
                )
                if cancel_invoices:
                    inv_update_ids.update(cancel_invoices.ids)
                    cancel_invoices.action_invoice_draft()
                    cancel_invoices.env.clear()
                    contract._update_invoice_lines(cancel_invoices)
                # If no invoices are left in cancel state, we rewind
                # the next_invoice_date for the contract to generate again
                else:
                    contract.rewind_next_invoice_date()
                    invoicer = contract.group_id._generate_invoices()
                    if not invoicer.invoice_ids:
                        invoicer.unlink()
            # Validate again modified invoices
            validate_invoices = invoice_obj.browse(list(inv_update_ids))
            validate_invoices.action_invoice_open()
        return True

    def _on_group_id_changed(self):
        """Remove lines of open invoices and generate them again
        """
        self._reset_open_invoices_job()
        for contract in self:
            # Update next_invoice_date of group if necessary
            if contract.group_id.next_invoice_date:
                next_invoice_date = contract.next_invoice_date
                group_date = contract.group_id.next_invoice_date
                if group_date > next_invoice_date:
                    contract.group_id._compute_next_invoice_date()
