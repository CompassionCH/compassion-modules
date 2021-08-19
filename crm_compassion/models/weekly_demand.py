##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck, Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import math
from datetime import datetime, timedelta

from odoo import api, models, fields

# Number of days a sponsorship must be active before Sub validation
SUB_DURATION = 90.0

# Number of weeks to take into consideration for average computations
STATS_DURATION = 52.0


class WeeklyDemand(models.Model):
    _inherit = "demand.weekly.demand"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # Demand fields
    number_children_website = fields.Integer(
        "Web demand",
        default=lambda self: self.env["res.config.settings"]
        .sudo()
        .get_param("number_children_website"),
    )
    number_children_ambassador = fields.Integer(
        "Ambassadors demand",
        default=lambda self: self.env["res.config.settings"]
        .sudo()
        .get_param("number_children_ambassador"),
    )
    number_sub_sponsorship = fields.Float(
        "SUB demand", default=lambda self: self._default_demand_sub()
    )
    number_children_events = fields.Float(
        "Events demand",
        compute="_compute_demand_events",
        inverse="_inverse_fields",
        store=True,
    )
    total_demand = fields.Integer(compute="_compute_demand_total", store=True)

    # Resupply fields
    average_unsponsored_web = fields.Float(
        "Web resupply", default=lambda self: self._default_unsponsored_web()
    )
    average_unsponsored_ambassador = fields.Float(
        "Ambassadors resupply",
        default=lambda self: self._default_unsponsored_ambassador(),
    )
    resupply_sub = fields.Float(
        "SUB resupply",
        compute="_compute_resupply_sub",
        store=True,
        inverse="_inverse_fields",
    )
    average_cancellation = fields.Float(
        "Sponsorship cancellations", default=lambda self: self._default_cancellation()
    )
    resupply_events = fields.Integer(
        "Events resupply",
        compute="_compute_demand_events",
        store=True,
        inverse="_inverse_fields",
    )
    total_resupply = fields.Integer(compute="_compute_resupply_total", store=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends("week_start_date", "week_end_date")
    @api.multi
    def _compute_demand_events(self):
        for week in self.filtered("week_start_date").filtered("week_end_date"):
            # Compute demand
            events = self.env["crm.event.compassion"].search(
                [
                    ("hold_start_date", "<=", week.week_end_date),
                    ("start_date", ">=", week.week_start_date),
                ]
            )
            week_start = week.week_start_date
            week_end = week.week_end_date
            allocate = 0
            for event in events:
                hold_start = event.hold_start_date
                event_start = event.start_date
                days_for_allocation = (event_start - hold_start).days + 1
                days_in_week = 7
                if week_start < hold_start:
                    days_in_week = (week_end - hold_start).days + 1
                elif week_end > event_start:
                    days_in_week = (event_start - week_start).days + 1
                allocate += (
                    float(event.number_allocate_children * days_in_week)
                    / days_for_allocation
                )

            # Compute resupply
            events = self.env["crm.event.compassion"].search(
                [
                    ("hold_end_date", ">=", week.week_start_date),
                    ("hold_end_date", "<=", week.week_end_date),
                ]
            )
            resupply = 0
            for event in events:
                resupply += event.number_allocate_children - event.planned_sponsorships

            week.number_children_events = allocate
            week.resupply_events = resupply

    @api.multi
    def _inverse_fields(self):
        """ Allow to manually set demand and resupply computed numbers. """
        pass

    @api.model
    def _default_demand_sub(self):
        """ Compute average of SUB since one year. """
        start_date = datetime.today() - timedelta(weeks=STATS_DURATION)
        website_medium = self.env.ref("utm.utm_medium_website").id
        sub_sponsored = self.env["recurring.contract"].search_count(
            [
                ("parent_id", "!=", False),
                ("start_date", ">=", start_date),
                ("medium_id", "!=", website_medium),
            ]
        )
        return float(sub_sponsored) // STATS_DURATION

    @api.depends(
        "number_children_website",
        "number_children_ambassador",
        "number_sub_sponsorship",
        "number_children_events",
    )
    @api.multi
    def _compute_demand_total(self):
        for week in self:
            week.total_demand = (
                week.number_children_website
                + week.number_sub_sponsorship
                + week.number_children_ambassador
                + week.number_children_events
            )

    @api.model
    def _default_unsponsored_web(self):
        """ Compute average of unsponsored children on the website since
        one year.
        """
        start_date = datetime.today() - timedelta(weeks=STATS_DURATION)
        website_medium = self.env.ref("utm.utm_medium_website").id
        web_sponsored = self.env["recurring.contract"].search_count(
            [("medium_id", "=", website_medium), ("start_date", ">=", start_date)]
        )
        allocate_per_week = (
            self.env["res.config.settings"].sudo().get_param("number_children_website")
        )
        return allocate_per_week - (float(web_sponsored) / STATS_DURATION)

    @api.model
    def _default_unsponsored_ambassador(self):
        """ Compute average of unsponsored children from ambassadors since
        one year.
        """
        start_date = datetime.today() - timedelta(weeks=STATS_DURATION)
        website_medium = self.env.ref("utm.utm_medium_website").id
        ambass_sponsored = self.env["recurring.contract"].search_count(
            [
                ("origin_id.type", "=", "partner"),
                ("origin_id.partner_id", "!=", False),
                ("origin_id.partner_id.user_ids", "!=", False),
                ("start_date", ">=", start_date),
                ("medium_id", "!=", website_medium),
            ]
        )
        allocate_per_week = (
            self.env["res.config.settings"]
                .sudo()
                .get_param("number_children_ambassador")
        )
        return allocate_per_week - (float(ambass_sponsored) / STATS_DURATION)

    @api.depends("week_start_date")
    @api.multi
    def _compute_resupply_sub(self):
        """ Compute SUB resupply. """
        sub_average = self._default_demand_sub()
        today = datetime.date.today()
        start_date = today - timedelta(weeks=STATS_DURATION)
        rejected_sub = (
            self.env["recurring.contract"]
                .search(
                [
                    ("parent_id", "!=", False),
                    ("start_date", ">=", start_date),
                    ("end_date", "!=", None),
                    ("medium_id.name", "!=", "internet"),
                ]
            )
            .filtered(lambda s: ((s.end_date - s.start_date).days <= SUB_DURATION))
        )
        sub_reject_average = len(rejected_sub) // STATS_DURATION
        for week in self:
            start_date = week.week_start_date - timedelta(days=SUB_DURATION)
            if start_date <= today:
                limit_date = week.week_end_date - timedelta(days=SUB_DURATION)
                sub = self.env["recurring.contract"].search_count(
                    [
                        ("parent_id", "!=", False),
                        ("start_date", ">=", start_date),
                        ("start_date", "<=", limit_date),
                        ("medium_id.name", "!=", "internet"),
                    ]
                )
                week.resupply_sub = sub * (sub_reject_average // sub_average or 1)
            else:
                week.resupply_sub = sub_reject_average

    @api.model
    def _default_cancellation(self):
        """ Compute average of sponsor cancellations since one year. """
        start_date = datetime.today() - timedelta(weeks=STATS_DURATION)
        depart = self.env.ref("sponsorship_compassion.end_reason_depart")
        cancellations = self.env["recurring.contract"].search_count(
            [
                ("type", "like", "S"),
                ("state", "=", "terminated"),
                ("end_reason_id", "!=", depart.id),
                ("end_date", ">=", start_date),
            ]
        )
        return float(cancellations) // STATS_DURATION

    @api.depends(
        "average_unsponsored_web",
        "average_cancellation",
        "resupply_sub",
        "resupply_events",
    )
    @api.multi
    def _compute_resupply_total(self):
        for week in self:
            week.total_resupply = math.floor(
                week.average_unsponsored_web
                + week.resupply_sub
                + week.average_cancellation
                + week.resupply_events
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ If we had more sponsored children from the than
        what we predict to allocate based on the system setting, make the
        prevision larger. """
        if vals["average_unsponsored_web"] < 0:
            vals["number_children_website"] -= vals["average_unsponsored_web"]
            vals["average_unsponsored_web"] = 0

        if vals["average_unsponsored_ambassador"] < 0:
            vals["number_children_ambassador"] -= vals["average_unsponsored_ambassador"]
            vals["average_unsponsored_ambassador"] = 0

        return super().create(vals)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_values(self):
        """ Returns the values of a given week. """
        self.ensure_one()
        return self.read(
            [
                "week_start_date",
                "week_end_date",
                "number_children_website",
                "number_children_ambassador",
                "number_sub_sponsorship",
                "number_children_events",
                "average_unsponsored_web",
                "average_unsponsored_ambassador",
                "resupply_sub",
                "average_cancellation",
                "resupply_events",
            ]
        )[0]

    def get_defaults(self):
        """ Returns the computation defaults in a dictionary. """
        web = (
            self.env["res.config.settings"].sudo().get_param("number_children_website")
        )
        ambassador = (
            self.env["res.config.settings"]
                .sudo()
                .get_param("number_children_ambassador")
        )
        return {
            "number_children_website": web,
            "number_children_ambassador": ambassador,
            "average_unsponsored_web": self._default_unsponsored_web(),
            "average_unsponsored_ambassador": self._default_unsponsored_ambassador(),
            "average_cancellation": self._default_cancellation(),
        }

    @api.multi
    def correct_event_resupply(self):
        """
        Action rule called to correct a negative event resupply.
        In that case we have more sponsorships planned from events than what
        we allocate for them. We assume the sponsorships will be made through
        the website, so we transfer the web resupply to the event resupply.
        :return: True
        """
        for demand in self:
            web_resupply = max(
                demand.average_unsponsored_web + demand.resupply_events, 0
            )
            demand.write(
                {"average_unsponsored_web": web_resupply, "resupply_events": 0}
            )
        return True
