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

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

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
        "recurring.contract", "Sponsorship", readonly=False, index=True
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
    project_suspended = fields.Boolean(related="project_id.hold_gifts", tracking=True)
    child_id = fields.Many2one(
        "compassion.child",
        "Child",
        related="sponsorship_id.child_id",
        store=True,
        readonly=False,
    )
    gift_type_id = fields.Many2one(
        "sponsorship.gift.type",
        "Sponsorship Gift Type",
        required=True,
        index=True,
        domain=[("gmc_gift_type", "!=", False)],
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", "gift_id", string="Invoice lines"
    )
    message_id = fields.Many2one(
        "gmc.message", "GMC message", copy=False, readonly=False
    )

    # Gift information
    ##################
    name = fields.Char(compute="_compute_name", translate=False)
    gmc_gift_id = fields.Char(copy=False)
    gift_date = fields.Date(
        compute="_compute_invoice_fields",
        store=True,
        readonly=False,
    )
    date_partner_paid = fields.Date(
        compute="_compute_invoice_fields", inverse=lambda g: True, store=True
    )
    date_sent = fields.Datetime(related="message_id.process_date", store=True)
    amount = fields.Monetary(
        compute="_compute_invoice_fields",
        inverse=lambda g: True,
        store=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        related="sponsorship_id.company_id",
        help="Field is retrieve from the associated sponsorship",
    )
    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_currency",
        compute_sudo=True,
        readonly=False,
    )
    currency_usd = fields.Many2one(
        "res.currency", compute="_compute_usd", readonly=False
    )
    exchange_rate = fields.Float(copy=False, digits=(12, 6))
    amount_us_dollars = fields.Float("Amount due", copy=False)
    instructions = fields.Char()
    gift_type = fields.Selection(related="gift_type_id.gmc_gift_type")
    attribution = fields.Selection(related="gift_type_id.gmc_attribution")
    sponsorship_gift_type = fields.Selection(related="gift_type_id.gmc_gift_type")
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
        tracking=True,
    )
    undeliverable_reason = fields.Selection(
        [
            ("Project Transitioned", "Project Transitioned"),
            ("Beneficiary Exited", "Participant Exited"),
            ("Participant Exited", "Participant Exited"),
            (
                "Beneficiary Exited/Whereabouts Unknown",
                "Participant Exited/Whereabouts Unknown",
            ),
            (
                "Participant Exited/Whereabouts Unknown",
                "Participant Exited/Whereabouts Unknown",
            ),
            (
                "Beneficiary Exited More Than 90 Days Ago",
                "Participant Exited More Than 90 Days Ago",
            ),
            (
                "Participant Exited More Than 90 Days Ago",
                "Participant Exited More Than 90 Days Ago",
            ),
        ],
        copy=False,
    )
    threshold_alert = fields.Boolean(
        help="Partner exceeded the maximum gift amount allowed",
        copy=False,
    )
    threshold_alert_type = fields.Char(copy=False)
    field_office_notes = fields.Char(copy=False)
    status_change_date = fields.Datetime()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends(
        "invoice_line_ids",
        "invoice_line_ids.parent_state",
        "invoice_line_ids.amount_currency",
    )
    def _compute_invoice_fields(self):
        for gift in self:
            invoice_lines = gift.invoice_line_ids
            pay_dates = (
                invoice_lines.filtered("last_payment").mapped("last_payment")
                or invoice_lines.mapped("date")
                or [fields.Date.today()]
            )
            gift.date_partner_paid = fields.Date.to_string(max(d for d in pay_dates))
            gift.gift_date = (
                max(
                    invoice_lines.mapped("move_id").mapped("invoice_date")
                    or invoice_lines.mapped("date")
                    or [fields.Date.today()]
                )
                or fields.Date.today()
            )
            gift.amount = sum(invoice_lines.mapped(lambda il: -il.amount_currency))

    def _compute_currency(self):
        # Set gift currency depending on its invoice currency
        for gift in self:
            gift.currency_id = (
                self.mapped("invoice_line_ids.move_id.currency_id")
                or self.sponsorship_id.company_id.currency_id
            )[:1]

    def _compute_name(self):
        for gift in self:
            if gift.gift_type != "Beneficiary Gift":
                name = gift.translate("gift_type")
            else:
                name = gift.translate("sponsorship_gift_type") + " " + _("Gift")

            if gift.sponsorship_id:
                name += " [" + gift.sponsorship_id.display_name + "]"
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

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals_list):
        """Try to find existing gifts before creating a new one."""
        gifts = self.browse()
        for vals in vals_list.copy():
            previous_gift = self._search_for_similar_pending_gifts(vals)
            if previous_gift:
                gifts += previous_gift._blend_in_other_gift(vals)
                vals_list.remove(vals)
                continue

            # If a gift for the same partner is to verify, put as well
            # the new one to verify.
            partner_id = (
                self.env["recurring.contract"]
                .browse(vals["sponsorship_id"])
                .partner_id.id
            )
            gift_to_verify = self.search_count(
                [("partner_id", "=", partner_id), ("state", "=", "verify")]
            )
            if gift_to_verify:
                vals["state"] = "verify"
        new_gifts = super().create(vals_list)
        for new_gift in new_gifts:
            if new_gift.invoice_line_ids:
                new_gift.invoice_line_ids.write({"gift_id": new_gift.id})
            new_gift._create_gift_message()
        return gifts + new_gifts

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
                ("gift_type_id", "=", vals["gift_type_id"]),
                ("attribution", "=", vals["attribution"]),
                ("gift_date", "like", str(gift_date)[:4]),
                ("sponsorship_gift_type", "=", vals.get("sponsorship_gift_type")),
                ("state", "in", ["draft", "verify"]),
            ],
            limit=1,
        )

    def _get_gift_from_reversal_invoice_line(self, invoice_line):
        if invoice_line.move_id.move_type in ["out_refund"]:
            return invoice_line.move_id.reversed_entry_id.invoice_line_ids.mapped(
                "gift_id"
            )
        else:
            return self.env[self._name]

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
            aggregated_amounts = self.amount + other_gift_vals.get("amount", 0)
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
        gifts = self.env[self._name]
        product = invoice_line.product_id
        sponsorship = invoice_line.contract_id
        if not product.sponsorship_gift_type_id:
            return gifts

        gift_vals = {
            "sponsorship_id": sponsorship.id,
            "invoice_line_ids": [(4, invoice_line.id)],
            "instructions": invoice_line.move_id.narration,
            "sponsorship_gift_type_id": product.sponsorship_gift_type_id.id,
        }

        if invoice_line.debit == 0 and invoice_line.credit > 0:
            gift = self.create(gift_vals)
            eligible, message = gift.is_eligible()
            if not eligible:
                gift.message_post(body=message)
                gift.action_verify()
            return gift
        else:
            for reversal_gift in self._get_gift_from_reversal_invoice_line(
                invoice_line
            ):
                blend_gift = reversal_gift._blend_in_other_gift(gift_vals)
                if reversal_gift.state in ["In Progress", "Delivered"]:
                    gifts += blend_gift
                elif reversal_gift.state in ["draft", "verify"]:
                    if float_is_zero(blend_gift.amount):
                        blend_gift.unlink()
                    else:
                        gifts += blend_gift
            if invoice_line.move_id.move_type not in ["out_refund"]:
                return self._search_for_similar_pending_gifts(
                    gift_vals
                )._blend_in_other_gift(gift_vals)
        return gifts

    def is_eligible(self):
        """Verifies the amount is within the thresholds and that the fcp
        is currently accepting gifts.
        """
        self.ensure_one()
        self = self.with_company(self.company_id)
        sponsorship = self.sponsorship_id
        if not sponsorship.is_active:
            return False, "Sponsorship is not active"
        if sponsorship.project_id.hold_gifts:
            return False, "Sponsorship may have a project with hold gifts"

        threshold_rule = self.env["gift.threshold.settings"].search(
            [
                ("gift_type_id", "=", self.gift_type_id.id),
            ],
        )
        if threshold_rule:
            if self.company_id.currency_id != self.invoice_line_ids.move_id.currency_id:
                current_rate = (
                    threshold_rule.currency_id.rate
                    / self.invoice_line_ids.move_id.currency_id.rate
                )
            else:
                current_rate = threshold_rule.currency_id.rate or 1.0

            minimum_amount = threshold_rule.min_amount
            maximum_amount = threshold_rule.max_amount
            this_amount = self.amount * current_rate

            if this_amount < minimum_amount:
                return (
                    False,
                    f"""Gift amount is smaller than minimal amount, Gift amount:
                    {round(this_amount, 2)}$,
                Minimal amount :{round(minimum_amount, 2)}$. """,
                )
            if this_amount > maximum_amount:
                return (
                    False,
                    f"""Gift amount is higher than maximum amount, Gift amount:
                    {round(this_amount, 2)}$,
                Maximum amount :{round(maximum_amount, 2)}$. """,
                )

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
                        ("gift_type_id", "=", self.gift_type_id.id),
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
                    return (
                        False,
                        f"""Yearly threshold exceed: total_amount:
                        {round(total_amount)}$, Yearly threshold:
                        {round(maximum_amount, 2)}*{round(
                            threshold_rule.gift_frequency, 2)}
                        = {round(maximum_amount * threshold_rule.gift_frequency, 2)}$
                        """,
                    )

        return True, ""

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
        self.write(data)

    @api.model
    def process_commkit(self, commkit_data):
        """ "
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
        return True

    def action_suspended(self):
        self.write({"state": "suspended"})
        return True

    def action_cancel(self):
        """Cancel Invoices and delete Gifts."""
        self.mapped("invoice_line_ids.move_id").button_draft()
        self.mapped("message_id").unlink()
        return self.unlink()

    def mark_sent(self):
        self.mapped("message_id").unlink()
        return self.write(
            {
                "state": "Delivered",
                "status_change_date": fields.Datetime.now(),
            }
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
        Notify users defined in settings.
        """
        notify_ids = self.env["res.config.settings"].get_param("gift_notify_ids")[0][2]
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
