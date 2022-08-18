##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


# For more readability we have split "res.partner" by functionality
# pylint: disable=R7980
class PartnerSponsorshipReport(models.Model):
    _inherit = "res.partner"

    end_period = fields.Date(compute="_compute_end_period")
    start_period = fields.Date(compute="_compute_start_period")

    related_active_sponsorships = fields.One2many(
        "recurring.contract",
        compute="_compute_related_active_sponsorship",
        readonly=False,
    )
    related_sponsorships = fields.One2many(
        "recurring.contract", compute="_compute_related_sponsorship", readonly=False
    )

    # sr -> Sponsorship Report
    sr_sponsorship = fields.Integer(
        "Number of sponsorship",
        compute="_compute_sr_sponsorship",
        help="Count only the sponsorships who "
             "are fully managed or those who are "
             "paid (not the correspondent).",
    )
    sr_nb_boy = fields.Integer("Number of boys", compute="_compute_boy")
    sr_nb_girl = fields.Integer("Number of girls", compute="_compute_girl")
    sr_time_fcp = fields.Integer(
        "Total hour spent at the FCP", compute="_compute_time_scp"
    )
    sr_nb_meal = fields.Integer("Number of meals served", compute="_compute_meal")
    sr_nb_bible = fields.Integer(
        "Number of bibles distributed", compute="_compute_nb_bible"
    )
    sr_nb_medic_check = fields.Integer(
        "Number of given medical checks", compute="_compute_medic_check"
    )
    sr_total_donation = fields.Monetary("Invoices", compute="_compute_total_donation")
    sr_total_gift = fields.Integer("Gift", compute="_compute_total_gift")

    def _compute_related_sponsorship(self):
        for partner in self:
            sponsorships = partner.sponsorship_ids
            sponsorships |= partner.member_ids.mapped("sponsorship_ids")
            partner.related_sponsorships = sponsorships

    def _compute_related_active_sponsorship(self):
        for partner in self:
            sponsorships = partner.related_sponsorships
            partner.related_active_sponsorships = sponsorships.filtered("is_active")

    def _compute_start_period(self):
        for partner in self:
            end = partner.end_period
            partner.start_period = fields.Date.to_string(end - relativedelta(months=12))

    def _compute_end_period(self):
        today = fields.Date.today()
        for partner in self:
            partner.end_period = today

    def _compute_sr_sponsorship(self):
        for partner in self:
            partner.sr_sponsorship = len(partner.related_active_sponsorships)

    def _compute_boy(self):
        for partner in self:
            partner.sr_nb_boy = len(
                partner.related_active_sponsorships.mapped("child_id").filtered(
                    lambda r: r.gender == "M"
                )
            )

    def _compute_girl(self):
        for partner in self:
            partner.sr_nb_girl = len(
                partner.related_active_sponsorships.mapped("child_id").filtered(
                    lambda r: r.gender == "F"
                )
            )

    def _compute_time_scp(self):
        def get_time_in_scp(sponsorship):
            nb_weeks = sponsorship.contract_duration // 7.0
            country = sponsorship.child_id.field_office_id
            return nb_weeks * country.fcp_hours_week

        for partner in self:
            total_day = sum(partner.related_sponsorships.mapped(get_time_in_scp))
            partner.sr_time_fcp = total_day

    def _compute_meal(self):
        def get_nb_meal(sponsorship):
            nb_weeks = sponsorship.contract_duration // 7.0
            country = sponsorship.child_id.field_office_id
            return nb_weeks * country.fcp_meal_week

        for partner in self:
            total_meal = sum(
                partner.related_sponsorships.filtered("global_id").mapped(get_nb_meal)
            )
            partner.sr_nb_meal = total_meal

    def _compute_medic_check(self):
        def get_nb_check(sponsorship):
            nb_year = sponsorship.contract_duration // 365
            country = sponsorship.child_id.field_office_id
            return nb_year * country.fcp_medical_check

        for partner in self:
            total_check = sum(
                partner.related_sponsorships.filtered("global_id").mapped(get_nb_check)
            )
            partner.sr_nb_medic_check = total_check

    def _compute_nb_bible(self):
        for partner in self:
            total_bible = len(partner.related_sponsorships.filtered("global_id"))
            partner.sr_nb_bible = total_bible

    def _compute_total_donation(self):
        def get_sum_invoice(_partner):
            invoices = self.env["account.move"].search(
                [
                    ("partner_id", "=", _partner.id),
                    ("move_type", "=", "out_invoice"),
                    ("payment_state", "=", "paid"),
                    ("invoice_category", "in", ["gift", "sponsorship", "fund"]),
                    ("last_payment", "<", _partner.end_period),
                    ("last_payment", ">", _partner.start_period),
                ]
            )
            return sum(invoices.mapped("amount_total"))

        for partner in self:
            sr_total_donation = get_sum_invoice(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    sr_total_donation += get_sum_invoice(member)
            partner.sr_total_donation = sr_total_donation

    def _compute_total_gift(self):
        def get_nb_gift(_partner):
            return self.env["account.move"].search_count(
                [
                    ("partner_id", "=", _partner.id),
                    ("invoice_category", "=", "gift"),
                    ("move_type", "=", "out_invoice"),
                    ("payment_state", "=", "paid"),
                    ("last_payment", "<", _partner.end_period),
                    ("last_payment", ">=", _partner.start_period),
                ]
            )

        for partner in self:
            sr_total_gift = get_nb_gift(partner)
            if partner.is_church:
                for member in partner.member_ids:
                    sr_total_gift += get_nb_gift(member)
            partner.sr_total_gift = sr_total_gift

    def open_sponsorship_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Sponsorship Report",
            "res_model": "res.partner",
            "view_mode": "form",
            "context": self.with_context(
                form_view_ref="sponsorship_compassion.sponsorship_report_form"
            ).env.context,
            "res_id": self.id,
        }

    def open_donation_details(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Donations details",
            "res_model": "account.move.line",
            "views": [
                [
                    self.env.ref(
                        "sponsorship_compassion" ".view_invoice_line_partner_tree"
                    ).id,
                    "list",
                ]
            ],
            "context": self.with_context(
                search_default_group_product=1,
                tree_view_ref="sponsorship_compassion"
                              ".view_invoice_line_partner_tree ",
            ).env.context,
            "domain": [
                "|",
                ("partner_id", "=", self.id),
                ("partner_id.church_id", "=", self.id),
                ("move_id.invoice_category", "in", ["gift", "sponsorship", "fund"]),
                ("move_type", "=", "out_invoice"),
                ("payment_state", "=", "paid"),
                ("last_payment", "<", self.end_period),
                ("last_payment", ">=", self.start_period),
            ],
        }
