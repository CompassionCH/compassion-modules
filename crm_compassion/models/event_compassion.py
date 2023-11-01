##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import math
from datetime import datetime, timedelta

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class EventCompassion(models.Model):
    """A Compassion event."""

    _name = "crm.event.compassion"
    _description = "Compassion event"
    _order = "start_date desc"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True, tracking=True)
    full_name = fields.Char(compute="_compute_full_name")
    type = fields.Selection(
        [
            ("stand", _("Stand")),
            ("concert", _("Concert")),
            ("presentation", _("Presentation")),
            ("meeting", _("Meeting")),
            ("sport", _("Sport event")),
            ("tour", _("Sponsor tour")),
        ],
        required=True,
        tracking=True,
    )
    start_date = fields.Datetime(required=True)
    year = fields.Char(compute="_compute_year", store=True)
    end_date = fields.Datetime(required=True)
    partner_id = fields.Many2one(
        "res.partner", "Venue", tracking=True, readonly=False, check_company=True
    )
    zip_id = fields.Many2one("res.city.zip", "Address", readonly=False)
    street = fields.Char()
    user_id = fields.Many2one(
        "res.users", "Responsible", tracking=True, readonly=False, check_company=True
    )
    hold_ids = fields.One2many("compassion.hold", "event_id", readonly=True)
    allocate_child_ids = fields.One2many(
        "compassion.child",
        compute="_compute_allocate_children",
        string="Allocated children",
        readonly=False,
    )
    effective_allocated = fields.Integer(compute="_compute_allocate_children")
    staff_ids = fields.Many2many(
        "res.partner",
        "partners_to_staff_event",
        "event_id",
        "partner_id",
        "Staff",
        tracking=True,
        readonly=False,
    )
    user_ids = fields.Many2many(
        "res.users",
        compute="_compute_users",
        tracking=True,
        readonly=False,
    )
    description = fields.Html()
    analytic_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        copy=False,
        readonly=False,
        check_company=True,
    )
    origin_id = fields.Many2one("recurring.contract.origin", "Origin", copy=False)
    contract_ids = fields.One2many(
        "recurring.contract", related="origin_id.contract_ids"
    )
    expense_line_ids = fields.One2many(
        "account.analytic.line",
        compute="_compute_expense_lines",
        string="Expenses",
        readonly=False,
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", "event_id", readonly=True, check_company=True
    )
    income_line_ids = fields.One2many(
        "account.move.line",
        compute="_compute_income_lines",
        string="Income",
        readonly=False,
    )
    total_expense = fields.Float(compute="_compute_expense", readonly=True, store=True)
    total_income = fields.Float(compute="_compute_income", readonly=True, store=True)
    balance = fields.Float(
        "Profit/Loss", compute="_compute_balance", readonly=True, store=True
    )
    currency_id = fields.Many2one("res.currency", related="analytic_id.currency_id")
    number_allocate_children = fields.Integer(
        "Number of children to allocate",
        tracking=True,
        required=True,
        default=0,
    )
    planned_sponsorships = fields.Integer(
        "Expected sponsorships", tracking=True, required=True, default=0
    )
    lead_id = fields.Many2one(
        "crm.lead", "Opportunity", tracking=True, readonly=False, check_company=True
    )
    won_sponsorships = fields.Integer(related="origin_id.won_sponsorships", store=True)
    conversion_rate = fields.Float(related="origin_id.conversion_rate", store=True)
    calendar_event_id = fields.Many2one("calendar.event", readonly=False)
    hold_start_date = fields.Date(required=True)
    hold_end_date = fields.Date()
    campaign_id = fields.Many2one("utm.campaign", "Campaign", readonly=False)

    # Multi-company
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        readonly=False,
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_expense_lines(self):
        for event in self:
            event.expense_line_ids = event.analytic_id.line_ids.filtered(
                lambda l: l.amount < 0.0
            )

    def _compute_income_lines(self):
        for event in self:
            event.income_line_ids = event.invoice_line_ids.filtered(
                lambda l: l.payment_state == "paid"
                and not l.contract_id
                and l.move_id.move_type == "out_invoice"
            )

    @api.depends("analytic_id.line_ids")
    def _compute_expense(self):
        for event in self:
            expenses = event.expense_line_ids.filtered(lambda l: l.amount < 0)
            event.total_expense = abs(sum(expenses.mapped("amount") or [0]))

    @api.depends("invoice_line_ids.payment_state")
    def _compute_income(self):
        for event in self:
            incomes = event.income_line_ids
            event.total_income = sum(incomes.mapped("price_subtotal") or [0])

    @api.depends("total_income", "total_expense")
    def _compute_balance(self):
        for event in self:
            event.balance = event.total_income - event.total_expense

    @api.depends("start_date")
    def _compute_year(self):
        for event in self:
            if event.start_date:
                event.year = str(event.start_date.year)
            else:
                event.year = False

    def _compute_full_name(self):
        for event in self:
            event.full_name = event.type.title() + " " + event.name + " " + event.year

    @api.depends("hold_ids", "hold_ids.type")
    def _compute_allocate_children(self):
        for event in self:
            children = event.hold_ids.mapped("child_id")
            event.allocate_child_ids = children
            nb_child = 0
            for child in children:
                if child.state == "N":
                    nb_child += 1
            event.effective_allocated = nb_child

    @api.constrains("hold_start_date", "start_date")
    def _check_hold_start_date(self):
        for event in self:
            if event.hold_start_date > event.start_date.date():
                raise ValidationError(
                    _("The hold start date must " "be before the event starting date !")
                )

    def compute_hold_start_date(self, start=None):
        delta = (
            self.env["res.config.settings"]
            .sudo()
            .get_param("days_allocate_before_event")
        )
        return (start if start else self.start_date.date()) - timedelta(days=delta)

    @api.depends("staff_ids")
    def _compute_users(self):
        for event in self:
            event.user_ids = event.staff_ids.mapped("user_ids").filtered(
                lambda u: not u.share
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_single
    def create(self, vals):
        """When an event is created:
        - Format the name to remove year of it,
        - Create an analytic_account,
        - Create an origin for sponsorships.
        """
        # Avoid putting twice the date in linked objects name
        event_year = str(datetime.today().year)
        if vals.get("start_date") and isinstance(vals["start_date"], str):
            event_year = str(fields.Date.from_string(vals["start_date"]).year)
        event_name = vals.get("name", "0000")
        if event_name[-4:] == event_year:
            vals["name"] = event_name[:-4]
        elif event_name[-2:] == event_year[-2:]:
            vals["name"] = event_name[:-2]

        # Compute hold_start_date from vals if it hasn't been set
        if not vals.get("hold_start_date"):
            hold_start_date = self.compute_hold_start_date(
                start=fields.Datetime.from_string(vals["start_date"])
            )
            vals["hold_start_date"] = hold_start_date

        event = super().create(vals)

        # Analytic account and Origin linked to this event
        analytic_id = (
            self.env["account.analytic.account"].create(event._get_analytic_vals()).id
        )
        origin_id = (
            self.env["recurring.contract.origin"]
            .create(event._get_origin_vals(analytic_id))
            .id
        )
        event.with_context(no_sync=True).write(
            {
                "origin_id": origin_id,
                "analytic_id": analytic_id,
            }
        )

        # Workaround, default_start_date must be removed from context,
        # details in commit
        context = dict(self._context)
        context.pop("default_start_date", None)
        calendar_obj = self.env["calendar.event"].with_context({}, context)

        # Add calendar event
        calendar_event = calendar_obj.create(event._get_calendar_vals())
        event.with_context(no_calendar=True).calendar_event_id = calendar_event

        return event

    def write(self, vals):
        """Push values to linked objects."""
        super().write(vals)
        if not self.env.context.get("no_sync"):
            for event in self:
                # Update Analytic Account and Origin
                event.analytic_id.write(event._get_analytic_vals())
                if "user_id" in vals and event.origin_id:
                    event.origin_id.partner_id = event.user_id.partner_id

                if "name" in vals:
                    # Only administrator has write access to origins.
                    self.env["recurring.contract.origin"].sudo().browse(
                        event.origin_id.id
                    ).write({"name": event.full_name})
                if not self.env.context.get("no_calendar"):
                    event.calendar_event_id.write(event._get_calendar_vals())

        return True

    def copy(self, default=None):
        this_year = str(datetime.now().year)
        if self.year == this_year:
            if default is None:
                default = {}
            default["name"] = self.name + " (copy)"
        return super().copy(default)

    def unlink(self):
        """Check that the event is not linked with expenses or won
        sponsorships."""
        for event in self:
            if event.contract_ids or event.balance:
                raise exceptions.UserError(
                    _(
                        "The event is linked to expenses or sponsorships. "
                        "You cannot delete it."
                    )
                )
            else:
                if event.analytic_id:
                    event.analytic_id.unlink()
                event.origin_id.unlink()
                event.calendar_event_id.unlink()
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def update_calendar_events(self):
        """Put calendar event for old events missing it."""
        events = self.with_context(no_calendar=True).search([])
        calendar_obj = self.env["calendar.event"]
        for event in events:
            calendar_vals = event._get_calendar_vals()
            if event.calendar_event_id:
                event.calendar_event_id.write(calendar_vals)
            else:
                calendar_event = calendar_obj.create(calendar_vals)
                event.calendar_event_id = calendar_event
        return True

    def force_update_won_sponsorships_count(self):
        for event in self:
            event.origin_id._compute_won_sponsorships()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def show_sponsorships(self):
        self.ensure_one()
        return {
            "name": _("Sponsorships"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "recurring.contract",
            "context": {
                "default_type": "S",
                "default_company_id": self.company_id.id,
                "default_origin_id": self.origin_id.id,
                "default_campaign_id": self.campaign_id.id,
                "search_default_origin_id": self.origin_id.id,
            },
        }

    def show_expenses(self):
        self.ensure_one()
        return {
            "name": _("Expenses"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "account.analytic.line",
            "context": {
                "default_account_id": self.analytic_id.id,
                "expense_from_event": True,
                "default_company_id": self.company_id.id,
                "search_default_account_id": self.analytic_id.id,
            },
        }

    def show_income(self):
        self.ensure_one()
        return {
            "name": _("Income"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "context": self.with_context(
                default_analytic_account_id=self.analytic_id.id,
                default_company_id=self.company_id.id,
                default_move_type="out_invoice",
                search_default_paid=True,
            ).env.context,
            "domain": [("id", "in", self.invoice_line_ids.mapped("move_id").ids)],
        }

    def show_children(self):
        return {
            "name": _("Allocated Children"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "compassion.child",
            "src_model": "crm.event.compassion",
            "context": self.with_context(search_default_available=1).env.context,
            "domain": [("id", "in", self.allocate_child_ids.ids)],
        }

    @api.onchange("start_date")
    def onchange_start_date(self):
        if self.start_date:
            self.hold_start_date = self.compute_hold_start_date()

    @api.onchange("end_date")
    def onchange_end_date(self):
        if self.end_date:
            days_after = self.env["res.config.settings"].get_param(
                "days_hold_after_event"
            )
            self.hold_end_date = (self.end_date + timedelta(days=days_after)).date()

    @api.onchange("partner_id")
    def onchange_partner(self):
        self.street = self.partner_id.street
        self.zip_id = self.partner_id.zip_id

    @api.onchange("lead_id")
    def onchange_lead_id(self):
        if self.lead_id.user_id:
            self.user_id = self.lead_id.user_id

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_analytic_vals(self):
        name = self.name
        if self.zip_id.city_id:
            name += " " + self.zip_id.city_id.name
        return {
            "name": name,
            "year": self.year,
            "partner_id": self.user_id.partner_id.id,
            "event_id": self.id,
        }

    def _get_origin_vals(self, analytic_id):
        return {
            "type": "event",
            "event_id": self.id,
            "analytic_id": analytic_id,
            "partner_id": self.user_id.partner_id.id,
        }

    def _get_calendar_vals(self):
        """
        Gets the calendar event values given the event
        :return: dictionary of calendar.event values
        """
        self.ensure_one()
        time_delta = self.end_date - self.start_date
        duration_in_hours = math.ceil(
            time_delta.days * 24 + time_delta.seconds / 3600.0
        )
        calendar_vals = {
            "name": self.name,
            "compassion_event_id": self.id,
            "categ_ids": [(6, 0, [self.env.ref("crm_compassion.calendar_event").id])],
            "duration": max(duration_in_hours, 3),
            "description": html2plaintext(self.description),
            "location": self.zip_id.city_id.name,
            "user_id": self.user_id.id,
            "partner_id": self.user_id.parent_id.id,
            "partner_ids": [
                (6, 0, (self.staff_ids | self.partner_id | self.user_id.partner_id).ids)
            ],
            "start": self.start_date,
            "stop": self.end_date or self.start_date,
            "allday": self.end_date and self.start_date.date() != self.end_date.date(),
        }
        return calendar_vals

    def allocate_children_action(self):
        no_money_yield = float(self.planned_sponsorships)
        yield_rate = float(self.number_allocate_children - self.planned_sponsorships)
        if self.number_allocate_children > 1:
            no_money_yield /= self.number_allocate_children
            yield_rate /= self.number_allocate_children
        expiration_date = self.end_date + timedelta(
            days=self.env["res.config.settings"].get_param("days_hold_after_event")
        )
        return {
            "name": _("Global Childpool"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "compassion.childpool.search",
            "target": "current",
            "context": self.with_context(
                {
                    "default_take": (
                        self.number_allocate_children - self.effective_allocated
                    ),
                    "default_event_id": self.id,
                    "default_channel": "event",
                    "default_ambassador": self.user_id.partner_id.id,
                    "default_source_code": self.name,
                    "default_no_money_yield_rate": no_money_yield * 100,
                    "default_yield_rate": yield_rate * 100,
                    "default_expiration_date": expiration_date,
                    "default_campaign_id": self.campaign_id.id,
                }
            ).env.context,
        }

    def allocate_children(self):
        """
        Puts children on hold for the event
        @return: Nothing
        """
        for event in self:
            context = event.allocate_children()["context"]
            childpool = (
                self.env["compassion.childpool.search"].with_context(context).create({})
            )
            childpool.rich_mix()
            hold_wizard = (
                self.env["child.hold.wizard"]
                .with_context(active_id=childpool.id, active_model=childpool._name)
                .create({})
            )
            hold_wizard.with_delay().send()

    ##########################################################################
    #              SUBSCRIPTION METHODS TO SUBSCRIBE STAFF ONLY              #
    ##########################################################################
    def message_auto_subscribe(self, updated_fields, values=None):
        """
        Subscribe from user_ids field which is a computed field.
        """
        if "staff_ids" in updated_fields and values:
            updated_fields = ["user_ids"]
            for event in self:
                users = event.user_ids
                # Subscribe each staff individually
                ambassador = event.user_id
                for user in users:
                    # Hack to address the mail to the correct user, change
                    # user_id field(bypass ORM to avoid tracking field change)
                    self.env.cr.execute(
                        "UPDATE crm_event_compassion "
                        f"SET user_id = {user.id} WHERE id = {event.id}"
                    )
                    values = {"user_ids": user.id}
                    super(EventCompassion, event).message_auto_subscribe(
                        updated_fields, values
                    )
                # Restore ambassador
                user_id = "NULL"
                if ambassador.id:
                    user_id = ambassador.id
                self.env.cr.execute(
                    "UPDATE crm_event_compassion "
                    f"SET user_id = {user_id} WHERE id = {event.id}"
                )
        return True

    @api.model
    def _message_get_auto_subscribe_fields(
        self, updated_fields, auto_follow_fields=None
    ):
        """Add user_ids field to followers"""
        auto_follow_fields = ["user_ids"]
        if "staff_ids" in updated_fields:
            updated_fields.append("user_ids")
        return super()._message_get_auto_subscribe_fields(
            updated_fields, auto_follow_fields
        )
