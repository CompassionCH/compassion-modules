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
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

INTERVENTION_PORTAL_URL = "https://compassion.force.com/GlobalPartners/"


class CompassionIntervention(models.Model):
    """All interventions on hold or sponsored."""

    _inherit = [
        "compassion.generic.intervention",
        "mail.thread",
        "compassion.mapped.model",
        "mail.activity.mixin",
    ]
    _name = "compassion.intervention"
    _description = "Intervention"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # General Information
    #####################
    state = fields.Selection(
        [
            ("on_hold", _("On Hold")),
            ("sla", _("SLA Negotiation")),
            ("committed", _("Committed")),
            ("active", _("Active")),
            ("close", _("Closed")),
            ("cancel", _("Cancelled")),
        ],
        default="on_hold",
        tracking=True,
    )
    type = fields.Selection(store=True)
    parent_intervention_name = fields.Char(string="Parent Intervention")
    intervention_status = fields.Selection(
        [
            ("Approved", _("Approved")),
            ("Cancelled", _("Cancelled")),
            ("Closed", _("Closed")),
            ("Draft", _("Draft")),
            ("Rejected", _("Rejected")),
            ("Submitted", _("Submitted")),
        ],
    )
    funding_global_partners = fields.Char()
    cancel_reason = fields.Char()
    fcp_ids = fields.Many2many(
        "compassion.project",
        "fcp_interventions",
        "intervention_id",
        "fcp_id",
        string="FCPs",
    )
    product_template_id = fields.Many2one(
        "product.template", "Linked product", readonly=False
    )
    subcategory_ids = fields.Many2many(
        "compassion.intervention.subcategory",
        "compassion_intervention_subcategory_rel",
        string="Subcategory",
    )

    # Multicompany
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company.id,
        readonly=False,
    )

    # Schedule Information
    ######################
    start_date = fields.Date(help="Actual start date")
    actual_duration = fields.Integer(help="Actual duration in months")
    initial_planned_end_date = fields.Date()
    planned_end_date = fields.Date(tracking=True)
    end_date = fields.Date(help="Actual end date", tracking=True)

    # Budget Information (all monetary fields are in US dollars)
    ####################
    estimated_local_contribution = fields.Float()
    impacted_beneficiaries = fields.Integer(
        help="Actual number of impacted beneficiaries"
    )
    local_contribution = fields.Float(help="Actual local contribution")
    commitment_amount = fields.Float(tracking=True)
    commited_percentage = fields.Float(tracking=True, default=100.0)
    total_expense = fields.Char("Total expense", compute="_compute_move_line")
    total_income = fields.Char("Total income", compute="_compute_move_line")
    total_amendment = fields.Float()
    total_actual_cost_local = fields.Float("Total cost (local currency)")
    total_estimated_cost_local = fields.Float("Estimated costs (local currency)")
    local_currency_id = fields.Many2one(
        "res.currency",
        related="field_office_id.country_id.currency_id",
        readonly=False,
    )

    # Intervention Details Information
    ##################################
    problem_statement = fields.Text()
    background_information = fields.Text()
    objectives = fields.Text()
    success_factors = fields.Text()
    solutions = fields.Text()
    not_funded_implications = fields.Text()
    implementation_risks = fields.Text()

    # Service Level Negotiation
    ###########################
    sla_negotiation_status = fields.Selection(
        [
            ("--None--", _("None")),
            ("FO Costs Proposed", _("FO Costs Proposed")),
            ("GP Accepted Costs", _("GP Accepted Costs")),
            ("GP Preferences Submitted", _("GP Preferences Submitted")),
            ("GP Rejected Costs", _("GP Rejected Costs")),
            ("FO Rejected GP Preferences", _("FO Rejected GP Preferences")),
        ],
        tracking=True,
    )
    sla_comments = fields.Char()
    fo_proposed_sla_costs = fields.Float(
        help="The costs proposed by the National Office for the SLA"
    )
    approved_sla_costs = fields.Float(
        help="The final approved Service Level Agreement Cost"
    )
    deliverable_level_1_ids = fields.Many2many(
        "compassion.intervention.deliverable",
        "compassion_intervention_deliverable1_rel",
        "intervention_id",
        "deliverable_id",
        string="Level 1 Deliverables",
        compute="_compute_level1_deliverables",
        readonly=False,
    )
    deliverable_level_2_ids = fields.Many2many(
        "compassion.intervention.deliverable",
        "compassion_intervention_deliverable2_rel",
        "intervention_id",
        "deliverable_id",
        string="Level 2 Deliverables",
    )
    deliverable_level_3_ids = fields.Many2many(
        "compassion.intervention.deliverable",
        "compassion_intervention_deliverable3_rel",
        "intervention_id",
        "deliverable_id",
        string="Level 3 Deliverables",
    )
    sla_selection_complete = fields.Boolean()

    # Hold information
    ##################
    hold_id = fields.Char()
    service_level = fields.Selection(
        [
            ("Level 1", _("Level 1")),
            ("Level 2", _("Level 2")),
            ("Level 3", _("Level 3")),
        ],
        required=True,
    )
    hold_amount = fields.Float(
        tracking=True,
    )
    expiration_date = fields.Date()
    next_year_opt_in = fields.Boolean()
    user_id = fields.Many2one(
        "res.users",
        "Primary owner",
        domain=[("share", "=", False)],
        tracking=True,
    )
    secondary_owner = fields.Char()

    # Survival Information
    ######################
    survival_slots = fields.Integer()
    launch_reason = fields.Char()
    mother_children_challenges = fields.Char("Challenges for mother and children")
    community_benefits = fields.Char()
    mother_average_age = fields.Integer("Avg age of first-time mother")
    household_children_average = fields.Integer("Avg of children per household")
    under_five_population = fields.Char("% population under age 5")
    birth_medical = fields.Char("% births in medical facility")
    spiritual_activity_ids = fields.Many2many(
        "fcp.spiritual.activity",
        "intervention_spiritual_activities",
        string="Spiritual activities",
    )
    cognitive_activity_ids = fields.Many2many(
        "fcp.cognitive.activity",
        "intervention_cognitive_activities",
        string="Cognitive activities",
    )
    physical_activity_ids = fields.Many2many(
        "fcp.physical.activity",
        "intervention_physical_activities",
        string="Physical activities",
    )
    socio_activity_ids = fields.Many2many(
        "fcp.sociological.activity",
        "intervention_socio_activities",
        string="Sociological activities",
    )
    activities_for_parents = fields.Char()
    other_activities = fields.Char()

    def _compute_level1_deliverables(self):
        for intervention in self:
            if not intervention.type:
                intervention.deliverable_level_1_ids = False
                continue
            if "CIV" in intervention.type:
                intervention.deliverable_level_1_ids = self.env.ref(
                    "intervention_compassion.deliverable_final_program_report"
                )
            elif "Survival" in intervention.type:
                intervention.deliverable_level_1_ids = (
                    self.env.ref("intervention_compassion.deliverable_icp_profile")
                    + self.env.ref(
                        "intervention_compassion."
                        "deliverable_survival_quarterly_report_data"
                    )
                    + self.env.ref(
                        "intervention_compassion."
                        "deliverable_survival_activity_report_lite"
                    )
                    + self.env.ref(
                        "intervention_compassion." "deliverable_survival_launch_budget"
                    )
                    + self.env.ref(
                        "intervention_compassion."
                        "deliverable_survival_community_information"
                    )
                )
            elif "Sponsorship" in intervention.type:
                intervention.deliverable_level_1_ids = (
                    self.env.ref("intervention_compassion.deliverable_icp_profile")
                    + self.env.ref(
                        "intervention_compassion."
                        "deliverable_icp_community_information"
                    )
                    + self.env.ref(
                        "intervention_compassion."
                        "deliverable_sponsorship_launch_budget"
                    )
                )
            else:
                intervention.deliverable_level_1_ids = False

    def _compute_move_line(self):
        for record in self:
            # Get the currency of the connected user's company
            currency_name = record.env.company.currency_id.name

            mv_line_expense = record.env["account.move.line"].search(
                [
                    ("product_id.product_tmpl_id", "=", record.product_template_id.id),
                    ("debit", ">", 0),
                    (
                        "account_id",
                        "=",
                        record.product_template_id.property_account_expense_id.id,
                    ),
                ]
            )
            mv_line_income = record.env["account.move.line"].search(
                [
                    ("product_id.product_tmpl_id", "=", record.product_template_id.id),
                    ("credit", ">", 0),
                    (
                        "account_id",
                        "=",
                        record.product_template_id.property_account_income_id.id,
                    ),
                ]
            )

            total_inc = sum(mv_line_income.mapped("credit"))
            total_exp = sum(mv_line_expense.mapped("debit"))
            record.total_income = f"{total_inc} {currency_name}"
            record.total_expense = f"{total_exp} {currency_name}"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if vals.get("service_level") != "Level 1":
            vals["state"] = "sla"
        vals["commited_percentage"] = 0
        intervention = super().create(vals)
        intervention.get_infos()
        intervention.fcp_ids.get_lifecycle_event()
        return intervention

    def write(self, vals):
        """
        When record is updated :

        - Update hold if values are changed.
        - Check SLA Negotiation modifications (in ir.action.rules)
        - Check end of intervention
        """
        hold_fields = [
            "hold_amount",
            "expiration_date",
            "next_year_opt_in",
            "user_id",
            "secondary_owner",
            "service_level",
        ]
        update_hold = False
        for field in hold_fields:
            if field in vals:
                update_hold = self.env.context.get("hold_update", True)
                break

        res = super().write(vals)

        if update_hold:
            self.update_hold()

        # Check closure of Intervention
        intervention_status = vals.get("intervention_status")
        if intervention_status in ("Cancelled", "Closed"):
            state = "close" if intervention_status == "Closed" else "cancel"
            super().write({"state": state})

        return res

    def unlink(self):
        """Only allow to delete cancelled Interventions."""
        if self.filtered(lambda i: i.state != "cancel"):
            raise UserError(_("You can only delete cancelled Interventions."))
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_intervention(self, commkit_data):
        # Two messages can call this method. Try to find which one.
        intervention_details_request = commkit_data.get(
            "GPInitiatedInterventionHoldNotification",
            commkit_data.get("InterventionOptInHoldNotification"),
        )
        intervention = self
        if intervention_details_request:
            vals = self.json_to_data(intervention_details_request)

            vals["total_cost"] = vals["hold_amount"] = float(
                vals["hold_amount"].replace("'", "").replace(",", "")
            )
            if "secondary_owner" in vals and not vals["secondary_owner"]:
                del vals["secondary_owner"]

            if "service_level" not in vals or not vals.get("service_level"):
                vals["service_level"] = "Level 1"

            intervention_name = vals["name"]

            if intervention_name.find("FY") != -1:
                split_name = intervention_name.split("FY")
                search_value = split_name[0] + "FY" + str(int(split_name[1]) - 1)
                last_intervention = self.search([("name", "=", search_value)])
                if last_intervention:
                    vals[
                        "product_template_id"
                    ] = last_intervention.product_template_id.id

            # By default we want to opt-in for next years
            vals["next_year_opt_in"] = True
            intervention = self.create(vals)

            # Once the intervention is created, send task for the primary owner
            if intervention:
                for user in intervention.user_id:
                    intervention.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary=_("Set an expiration date and service level"),
                        note=_(
                            "You have been assigned to the Intervention {}. "
                            "Please update the intervention by setting an "
                            "expiration date and service level.".format(
                                intervention.intervention_id
                            )
                        ),
                        user_id=user.id,
                    )

        return intervention.ids

    @api.model
    def update_intervention_details_request(self, commkit_data):
        """This function is automatically executed when a
        UpdateInterventionDetailsRequest Message is received. It will
        convert the message from json to odoo format and then update the
        concerned records
        :param commkit_data contains the data of the
        message (json)
        :return list of intervention ids which are concerned by the
        message"""
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        intervention_request = (
            commkit_data.get(
                "InterventionDetailsRequest",
                commkit_data.get("InterventionAmendmentKitRequest"),
            )
            or []
        )
        intervention_local_ids = []
        # For each dictionary, we update the corresponding record
        for idr in intervention_request:
            vals = self.json_to_data(idr)
            intervention_id = vals["intervention_id"]

            intervention = self.search([("intervention_id", "=", intervention_id)])
            if intervention:
                intervention_local_ids.append(intervention.id)
                intervention.with_context(hold_update=False).write(vals)
                intervention.message_post(
                    body=_("The information of this intervention have been updated"),
                    subject=(_(intervention.name + "got an Update")),
                    message_type="email",
                    subtype_xmlid="mail.mt_comment",
                )

        return intervention_local_ids

    def update_hold(self):
        if not self.hold_id:
            return True
        action_id = self.env.ref(
            "intervention_compassion.intervention_update_hold_action"
        ).id
        message = (
            self.env["gmc.message"]
            .with_context(async_mode=False)
            .create({"action_id": action_id, "object_id": self.id})
        )
        if "failure" in message.state:
            raise UserError(message.failure_reason)
        return True

    def hold_sent(self, intervention_vals=None):
        """Do nothing when hold is sent."""
        return True

    def hold_cancelled(self, intervention_vals=None):
        """Remove the hold and put intervention in Cancel state."""
        self.write(
            {
                "hold_id": False,
                "state": "cancel",
            }
        )
        self.message_post(
            body=_("The hold of %s (%s) was just cancelled.")
            % (self.name, self.intervention_id),
            subject=_("Intervention hold cancelled"),
            partner_ids=self.message_partner_ids.ids,
            subtype_xmlid="mail.mt_comment",
        )

    @api.model
    def auto_subscribe(self):
        """
        Method added to auto subscribe users after migration
        """
        interventions = self.search([("user_id", "!=", False)])
        for intervention in interventions:
            vals = {"user_id": intervention.user_id.id}
            intervention.message_auto_subscribe(["user_id"], vals)
        return True

    @api.model
    def commited_percent_change(self, commkit_data):
        """
        Called when GMC message received
        :param commkit_data: json data
        :return: list of ids updated
        """
        json_data = commkit_data.get("InterventionCommittedPercentChangeNotification")
        intervention_id = json_data.get("Intervention_ID")
        intervention = self.search([("intervention_id", "=", intervention_id)])
        if intervention:
            intervention.commited_percentage = json_data.get("CommittedPercent", 100)
            intervention.message_post(
                body=_("The commitment percentage has changed."),
                message_type="email",
                subtype_xmlid="mail.mt_comment",
            )
        return intervention.ids

    def link_product(self):
        # search existing project or create a new one if doesn't exist.
        for intervention in self:
            if (
                intervention.product_template_id
                or intervention.state != "committed"
                or not intervention.parent_intervention_name
            ):
                continue
            product_name = intervention.parent_intervention_name
            product_price = intervention.total_cost
            product = intervention.env["product.template"].search(
                [["name", "=", product_name]]
            )
            intervention.product_template_id = (
                product
                if product
                else intervention.env["product.template"].create(
                    {
                        "name": product_name,
                        "type": "service",
                        "list_price": product_price,
                        "intervention_id": None,
                    }
                )
            )

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def show_expenses(self):
        return {
            "name": _("Expenses"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "account.move.line",
            "context": self.env.context,
            "domain": [
                ("product_id.product_tmpl_id", "=", self.product_template_id.id),
                ("debit", ">", 0),
                (
                    "account_id",
                    "=",
                    self.product_template_id.property_account_expense_id.id,
                ),
            ],
        }

    def show_income(self):
        return {
            "name": _("Income"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "account.move.line",
            "context": self.env.context,
            "domain": [
                ("product_id.product_tmpl_id", "=", self.product_template_id.id),
                ("credit", ">", 0),
                (
                    "account_id",
                    "=",
                    self.product_template_id.property_account_income_id.id,
                ),
            ],
        }

    def show_contract(self):
        return {
            "name": _("Contract"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "recurring.contract.line",
            "context": self.env.context,
            "domain": [
                ("product_id.product_tmpl_id", "=", self.product_template_id.id)
            ],
        }

    def show_partner(self):
        contracts = self.env["recurring.contract"].search(
            [
                ("type", "not in", ["S", "SC", "SWP"]),
                (
                    "contract_line_ids.product_id.product_tmpl_id",
                    "=",
                    self.product_template_id.id,
                ),
            ]
        )

        move_lines = self.env["account.move.line"].search(
            [
                ("product_id.product_tmpl_id", "=", self.product_template_id.id),
                ("credit", ">", 0),
            ]
        )

        return {
            "name": _("Partner"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "res.partner",
            "context": self.env.context,
            "domain": [
                "|",
                ("id", "in", contracts.mapped("partner_id.id")),
                ("id", "in", move_lines.mapped("partner_id.id")),
            ],
        }

    def get_infos(self):
        """Get the most recent information about the intervention"""
        for intervention in self:
            if intervention.state == "cancel":
                continue
            action_id = intervention.env.ref(
                "intervention_compassion.intervention_details_request"
            ).id

            message_vals = {
                "action_id": action_id,
                "object_id": intervention.id,
            }
            message = (
                intervention.env["gmc.message"]
                .with_context(hold_update=False)
                .create(message_vals)
            )
            if "failure" in message.state:
                raise UserError(message.failure_reason)
        return True

    def cancel_hold(self):
        action_id = self.env.ref(
            "intervention_compassion.intervention_cancel_hold_action"
        ).id
        message = (
            self.env["gmc.message"]
            .with_context(async_mode=False)
            .create({"action_id": action_id, "object_id": self.id})
        )
        if "failure" in message.state:
            raise UserError(message.failure_reason)
        return True

    def create_commitment(self):
        self.ensure_one()
        return {
            "name": _("Intervention Commitment Request"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "compassion.intervention.commitment.wizard",
            "context": self.with_context(
                {
                    "default_intervention_id": self.id,
                    "default_commitment_amount": self.hold_amount,
                }
            ).env.context,
            "target": "new",
        }

    def intervention_hold_removal_notification(self, commkit_data):
        """
        This function is automatically executed when a
        InterventionHoldRemovalNotification Message is received. It will
        convert the message from json to odoo format and then update the
        concerned records
        :param commkit_data contains the data of the message (json)
        :return list of intervention ids which are concerned by the message
        """
        # Apparently this message contains a single dictionary, and not a
        # list of dictionaries,
        ihrn = commkit_data["InterventionHoldRemovalNotification"]
        # Remove problematic type as it is not needed and contains
        # erroneous data
        del ihrn["InterventionType_Name"]

        vals = self.json_to_data(ihrn)
        intervention_id = vals["intervention_id"]

        intervention = self.env["compassion.intervention"].search(
            [
                ("intervention_id", "=", intervention_id),
                ("hold_id", "=", vals["hold_id"]),
            ]
        )
        if intervention:
            intervention.with_context(hold_update=False).write(vals)
            intervention.hold_cancelled()

        return [intervention.id]

    @api.model
    def intervention_reporting_milestone(self, commkit_data):
        """This function is automatically executed when a
        InterventionReportingMilestoneRequestList is received,
        it sends a message to the follower of the Intervention
        :param commkit_data contains the data of the
        message (json)
        :return list of intervention ids which are concerned by the
        message"""
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        milestones_data = commkit_data["InterventionReportingMilestoneRequestList"]
        intervention_local_ids = []

        for milestone in milestones_data:
            milestone_id = milestone.get("InterventionReportingMilestone_ID")
            intervention_id = milestone.get("Intervention_ID")
            intervention = self.search([("intervention_id", "=", intervention_id)])
            if intervention:
                intervention_local_ids.append(intervention.id)
                body = "A new milestone is available"
                if milestone_id:
                    milestone_url = INTERVENTION_PORTAL_URL + milestone_id
                    body += (
                        f' at <a href="{milestone_url}" '
                        f'target="_blank">{milestone_url}</a>.'
                    )
                intervention.message_post(
                    body=body,
                    subject=(_(intervention.name + ": New milestone " "received.")),
                    message_type="email",
                    subtype_xmlid="mail.mt_comment",
                )
        return intervention_local_ids

    @api.model
    def intervention_amendement_commitment(self, commkit_data):
        """This function is automatically executed when a
        InterventionAmendmentCommitmentNotification is received,
        it send a message to the follower of the Intervention,
        and update it
        :param commkit_data contains the data of the
               message (json)
        :return list of intervention ids which are concerned
                by the message"""
        # sleep to prevent a concurence error
        time.sleep(10)
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        interventionamendment = commkit_data.get(
            "InterventionAmendmentCommitmentNotification",
            commkit_data.get("InterventionAmendmentKitRequest", [{}])[0],
        )
        intervention_local_ids = []
        v = self.json_to_data(commkit_data)
        intervention_id = v["intervention_id"]
        amendment_amount = interventionamendment["AdditionalAmountRequestedUSD"]
        intervention = self.env["compassion.intervention"].search(
            [("intervention_id", "=", intervention_id)]
        )

        if intervention:
            if amendment_amount:
                intervention.total_amendment += amendment_amount
            intervention.get_infos()
            intervention_local_ids.append(intervention.id)
            amendment_type = ", ".join(interventionamendment.get("AmendmentType", []))
            amendment_reason = interventionamendment.get("ReasonsForAmendment", "")
            amendment_hold_id = interventionamendment.get("HoldID", "")
            body = (
                _("This intervention has been modified by amendment.")
                + f"""<br/>
                <ul>
                    <li>Amendment ID:
                    {interventionamendment['InterventionAmendment_ID']}</li>
                    <li>Amendment Type: {amendment_type}</li>
                    <li>Amendment Reason: {amendment_reason}</li>
                    <li>Amendment Amount: {amendment_amount}</li>
                    <li>Hold ID: {amendment_hold_id}</li>
                </ul>
                """
            )
            intervention.message_post(
                body=body,
                subject=_(intervention.name + ": Amendment received"),
                message_type="email",
                subtype_xmlid="mail.mt_comment",
            )

        return intervention_local_ids

    def json_to_data(self, json, mapping_name=None):
        json = json.get("InterventionAmendmentKitRequest", json)
        if "ICP" in json and json["ICP"] is not None:
            json["ICP"] = json["ICP"].split("; ")
        return super().json_to_data(json, mapping_name)


class InterventionDeliverable(models.Model):
    _name = "compassion.intervention.deliverable"
    _inherit = "connect.multipicklist"
    _description = "Intervention deliverable"

    res_model = "compassion.intervention"
    res_field = "deliverable_level_2_ids"
