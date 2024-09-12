##############################################################################
#
#    Copyright (C) 2014-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import functools
import random
import string

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .contracts import SPONSORSHIP_TYPE_LIST


# For more flexibility we have split "res.partner" by functionality
# pylint: disable=R7980
class ResPartner(models.Model):
    _inherit = ["res.partner", "compassion.mapped.model"]
    _name = "res.partner"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    portal_sponsorships = fields.Selection(
        [
            ("all", "All (partner is the correspondent and/or the payer)"),
            ("all_info", "All + correspondence info shown to payer only."),
            ("correspondent", "Correspondent (Children the partner corresponds with)"),
        ],
        "Sponsorships accessible from the portal",
        default="correspondent",
        required=True,
    )
    global_id = fields.Char(copy=False, readonly=True)
    contracts_fully_managed = fields.One2many(
        "recurring.contract",
        compute="_compute_related_contracts",
        string="Fully managed sponsorships",
    )
    contracts_paid = fields.One2many(
        "recurring.contract",
        compute="_compute_related_contracts",
        string="Sponsorships as payer only",
    )
    contracts_correspondant = fields.One2many(
        "recurring.contract",
        compute="_compute_related_contracts",
        string="Sponsorships as correspondant only",
    )
    sponsorship_ids = fields.One2many(
        "recurring.contract",
        compute="_compute_related_contracts",
    )
    other_contract_ids = fields.One2many(
        "recurring.contract",
        compute="_compute_related_contracts",
        string="Other contracts",
    )
    unrec_items = fields.Integer(compute="_compute_count_items")
    receivable_items = fields.Integer(compute="_compute_count_items")
    has_sponsorships = fields.Boolean()
    number_sponsorships = fields.Integer(string="Number of sponsorships", copy=False)
    preferred_name = fields.Char()
    sponsored_child_ids = fields.One2many(
        "compassion.child",
        "sponsor_id",
        "Sponsored children",
        readonly=False,
    )
    number_children = fields.Integer(
        string="Number of children",
        related="number_sponsorships",
    )
    member_ids = fields.One2many(
        "res.partner",
        "church_id",
        "Members",
        domain=[("active", "=", True)],
        readonly=False,
    )
    is_church = fields.Boolean(
        string="Is a Church", compute="_compute_is_church", store=True
    )
    church_member_count = fields.Integer(compute="_compute_is_church", store=True)
    church_id = fields.Many2one(
        "res.partner", "Church", domain=[("is_church", "=", True)], readonly=False
    )
    gmc_gender = fields.Char(compute="_compute_gmc_gender")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_related_contracts(self):
        """Returns the contracts of the sponsor of given type
        ('fully_managed', 'correspondent' or 'payer')
        """
        contract_obj = self.env["recurring.contract"]
        for partner in self:
            partner.contracts_correspondant = contract_obj.search(
                [
                    ("correspondent_id", "=", partner.id),
                    ("type", "in", SPONSORSHIP_TYPE_LIST),
                    ("fully_managed", "=", False),
                ],
                order="start_date desc",
            ).contract_line_ids.contract_id
            partner.contracts_paid = contract_obj.search(
                [
                    ("partner_id", "=", partner.id),
                    ("type", "in", SPONSORSHIP_TYPE_LIST),
                    ("fully_managed", "=", False),
                ],
                order="start_date desc",
            ).contract_line_ids.contract_id
            partner.contracts_fully_managed = contract_obj.search(
                [
                    ("partner_id", "=", partner.id),
                    ("type", "in", SPONSORSHIP_TYPE_LIST),
                    ("fully_managed", "=", True),
                ],
                order="start_date desc",
            ).contract_line_ids.contract_id
            partner.sponsorship_ids = (
                partner.contracts_correspondant
                + partner.contracts_paid
                + partner.contracts_fully_managed
            )
            partner.other_contract_ids = (
                contract_obj.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("type", "not in", SPONSORSHIP_TYPE_LIST),
                    ],
                    order="start_date desc",
                ).ids
                or False
            )

    def _compute_count_items(self):
        move_line_obj = self.env["account.move.line"]
        for partner in self:
            partner.unrec_items = move_line_obj.search_count(
                [
                    ("partner_id", "=", partner.id),
                    ("reconciled", "=", False),
                    ("account_id.reconcile", "=", True),
                    ("account_id.code", "=", "1050"),
                    ("parent_state", "=", "posted"),
                ]
            )
            partner.receivable_items = move_line_obj.search_count(
                [("partner_id", "=", partner.id), ("account_id.code", "=", "1050")]
            )

    def update_number_sponsorships(self):
        for partner in self:
            partner.number_sponsorships = self.env["recurring.contract"].search_count(
                partner._get_active_sponsorships_domain()
            )
            partner.has_sponsorships = partner.number_sponsorships
        return True

    @api.depends("category_id", "member_ids")
    def _compute_is_church(self):
        """Tell if the given Partners are Church Partners
        (by looking at their categories)."""

        # Retrieve all the categories and check if one is Church
        church_category = (
            self.env["res.partner.category"]
            .with_context(lang="en_US")
            .sudo()
            .search([("name", "=", "Church")], limit=1)
        )
        for record in self:
            is_church = False
            if church_category in record.category_id:
                is_church = True

            record.church_member_count = len(record.member_ids)
            record.is_church = is_church

    def _compute_gmc_gender(self):
        male = "Male"
        female = "Female"
        unknown = "Unkown"
        unset = "Not Applicable"
        title_mapping = {
            "Mister": male,
            "Madam": female,
            "Miss": female,
            "Doctor": unknown,
            "Professor": unknown,
            "Misters": male,
            "Ladies": female,
            "Mister and Madam": unset,
            "Friends of Compassion": unset,
            "Family": unset,
        }
        for partner in self:
            title = partner.with_context(lang="en_US").title.name
            partner.gmc_gender = title_mapping.get(title, unknown)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals_list):
        # Put a preferred name
        partners = super().create(vals_list)
        for partner in partners:
            if not partner.preferred_name:
                partner.preferred_name = (
                    partner.firstname or partner.lastname or partner.name
                )
            if not partner.ref:
                partner.ref = self.env["ir.sequence"].next_by_code("partner.ref")
        return partners

    def write(self, vals):
        if "firstname" in vals and "preferred_name" not in vals:
            vals["preferred_name"] = vals["firstname"]
        res = super().write(vals)

        if "church_id" in vals:
            self.mapped("church_id").update_number_sponsorships()

        notify_vals = [
            "firstname",
            "lastname",
            "name",
            "preferred_name",
            "title",
        ]
        notify = functools.reduce(
            lambda prev, val: prev or val in vals, notify_vals, False
        )

        if notify and not self.env.context.get("no_upsert"):
            self.filtered("global_id").upsert_constituent()

        self._updt_invoices_rp(vals)
        return res

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def show_lines(self):
        action = {
            "name": _("Related invoice lines"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "views": [
                (
                    self.env.ref(
                        "sponsorship_compassion.view_invoice_line_partner_tree"
                    ).id,
                    "tree",
                ),
                (False, "form"),
            ],
            "res_model": "account.move.line",
            "target": "current",
            "context": self.with_context(
                search_default_partner_id=self.ids
            ).env.context,
            "domain": self.env.context.get("domain", []),
        }

        return action

    def show_move_lines(self):
        tree_view_id = self.env.ref("account.view_move_line_tree").id
        form_view_id = self.env.ref("account.view_move_line_form").id
        action = {
            "name": _("Unreconciled Items"),
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "account.move.line",
            "view_id": tree_view_id,
            "views": [(tree_view_id, "tree"), (form_view_id, "form")],
            "target": "current",
            "context": self.with_context(
                search_default_partner_id=self.ids, search_default_posted=1
            ).env.context,
        }
        return action

    def create_contract(self):
        self.ensure_one()
        context = self.with_context(
            {
                "default_partner_id": self.id,
                "default_type": "S",
                "type": "S",
            }
        ).env.context
        return {
            "type": "ir.actions.act_window",
            "name": _("New Sponsorship"),
            "view_mode": "form",
            "res_model": "recurring.contract",
            "target": "current",
            "context": context,
        }

    def unreconciled_transaction_items(self):
        account_ids = self.env["account.account"].search([("code", "=", "1050")]).ids

        return self.with_context(
            search_default_unreconciled=1, search_default_account_id=account_ids[0]
        ).show_move_lines()

    def open_contracts(self):
        """Used to bypass opening a contract in popup mode from
        res_partner view."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contracts",
            "res_model": "recurring.contract",
            "views": [[False, "tree"], [False, "form"]],
            "domain": self._get_active_sponsorships_domain(),
        }

    def open_sponsored_children(self):
        self.ensure_one()
        children = (
            self.env["recurring.contract"]
            .search(self._get_active_sponsorships_domain())
            .mapped("child_id")
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Children",
            "res_model": "compassion.child",
            "view_mode": "tree,form",
            "domain": [("id", "in", children.ids)],
        }

    @api.onchange("lastname", "firstname")
    def onchange_preferred_name(self):
        self.preferred_name = self.firstname or self.name

    def forget_me(self):
        """Anonymize partner and delete sensitive data.
        This will call the GDPR Data Protection Request on Connect,
        Remove all letters and communication history, and attachments.
        """
        if self.global_id:
            action = self.env.ref("sponsorship_compassion.anonymize_partner")
            message = (
                self.env["gmc.message"]
                .with_context(async_mode=False)
                .create(
                    {
                        "action_id": action.id,
                        "object_id": self.id,
                        "partner_id": self.id,
                    }
                )
            )
            if "failure" in message.state:
                answer = message.get_answer_dict()
                if isinstance(answer, dict):
                    error_message = answer.get(
                        "DataProtection Error", message.failure_reason
                    )
                else:
                    error_message = message.failure_reason
                raise UserError(error_message)
        self.anonymize()
        # Reload the view
        return {"type": "ir.actions.client", "tag": "reload"}

    def anonymize(self, vals=None):
        # Called after Forget Me message sent to GMC. Anonymize all data from partner.
        self.ensure_one()
        partner = self.with_context(no_upsert=True, tracking_disable=True).sudo()

        def _random_str():
            return "".join([random.choice(string.ascii_letters) for n in range(8)])

        # referenced users are unlinked to avoid error when self.active is set to False
        partner.user_ids.unlink()

        # Anonymize and delete partner data
        partner.write(
            {
                "name": _random_str(),
                "firstname": False,
                "preferred_name": False,
                "parent_id": False,
                "image_1920": False,
                "phone": False,
                "mobile": False,
                "email": False,
                "street": _random_str(),
                "street2": _random_str(),
                "website": False,
                "function": False,
                "category_id": [(5, 0, 0)],
                "comment": False,
                "active": False,
                "city": False,
                "zip": False,
                "commercial_company_name": False,
                "company_name": False,
                "display_name": False,
                "partner_latitude": False,
                "partner_longitude": False,
                "lang": False,
                "title": False,
                "country_id": False,
                "uuid": False,
            }
        )
        partner.env["mail.mail"].search([("recipient_ids", "=", partner.id)]).unlink()
        partner.env["ir.attachment"].search(
            [("res_model", "=", "res.partner"), ("res_id", "=", partner.id)]
        ).unlink()

        # ---------- Remove banking information ----------
        # Get partner_bank_ids for partner_id = self.id
        partner_bank_ids = (
            partner.env["res.partner.bank"]
            .search([("partner_id", "=", partner.id)])
            .ids
        )

        # Update account_payment_line set partner_bank_id to NULL
        payment_lines = partner.env["account.payment.line"].search(
            [("partner_bank_id", "in", partner_bank_ids)]
        )
        payment_lines.write({"partner_bank_id": False})

        # Update account_move set partner_bank_id to NULL
        account_moves = partner.env["account.move"].search(
            [("partner_bank_id", "in", partner_bank_ids)]
        )
        account_moves.write({"partner_bank_id": False})

        partner.bank_ids.unlink()
        # ---------- End of Remove banking information ----------

        partner.env["gmc.message"].search([("partner_id", "=", partner.id)]).write(
            {"res_name": partner.name}
        )
        # Delete message and mail history
        partner.env["ir.attachment"].search(
            [("res_model", "=", self._name), ("res_id", "=", partner.id)]
        ).unlink()
        partner.message_follower_ids.unlink()
        partner.with_delay().clear_message_history()
        return True

    def clear_message_history(self):
        return (
            self.env["mail.message"]
            .search([("model", "=", self._name), ("res_id", "in", self.ids)])
            .unlink()
        )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def upsert_constituent(self):
        """UPSERT Constituent in GMC."""
        message_obj = self.env["gmc.message"].with_context(async_mode=False)
        messages = message_obj
        action_id = self.env.ref("sponsorship_compassion.upsert_partner").id
        for partner in self:
            if not partner.ref:
                partner.ref = self.env["ir.sequence"].next_by_code("partner.ref")
            # UpsertConstituent Message if not one already pending
            message_vals = {
                "action_id": action_id,
                "object_id": partner.id,
                "partner_id": partner.id,
            }
            messages += message_obj.create(message_vals)
        return messages

    def _get_active_sponsorships_domain(self):
        """
        Get a search domain to fetch active sponsorships of the given
        partners.
        :return: domain search filter for recurring.contract object
        """
        return [
            "|",
            ("partner_id", "in", self.ids),
            ("correspondent_id", "in", self.ids),
            ("activation_date", "!=", False),
            ("state", "not in", ["cancelled", "terminated"]),
            ("child_id", "!=", False),
        ]

    @api.model
    def json_to_data(self, json, mapping_name=None):
        if "GPID" in json:
            json["GPID"] = json["GPID"][3:]

        connect_data = super().json_to_data(json, mapping_name)

        if not connect_data.get("GlobalID") and "GlobalID" in connect_data:
            del connect_data["GlobalID"]

        return connect_data

    def get_portal_sponsorships(self, states=None):
        """
        Returns the sponsorships that can be displayed in the portal for the sponsor.
        :param states: Optional desired states of sponsorships displayed
        :return: recurring.contract recordset
        """
        self.ensure_one()
        if self.portal_sponsorships in ["all", "all_info"]:
            sponsorships = self.sponsorship_ids
        else:
            sponsorships = self.contracts_correspondant + self.contracts_fully_managed
        if states is not None:
            if not isinstance(states, list):
                states = [states]
            sponsorships = sponsorships.filtered(lambda s: s.state in states)
        return sponsorships

    def _updt_invoices_rp(self, vals):
        """
        It updates the invoices of a partner when the partner is updated.
        Should be called after the write has been done

        :param vals: the values that are being updated on the partner
        """
        payment_term_id = vals.get("property_payment_term_id")
        if payment_term_id:
            invoices = self.env["account.move"].search(
                [
                    ("partner_id", "in", self.ids),
                    ("payment_state", "=", "not_paid"),
                    ("state", "!=", "cancel"),
                    ("invoice_payment_term_id", "!=", payment_term_id),
                ]
            )
            data_invs = invoices._build_invoices_data(payment_term_id=payment_term_id)
            if data_invs:
                invoices.update_open_invoices(data_invs)
