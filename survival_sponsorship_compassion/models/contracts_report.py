from odoo import fields, models


# For more readability we have split "res.partner" by functionality
# pylint: disable=R7980
class PartnerSponsorshipReport(models.Model):
    _inherit = "res.partner"

    # sr -> Sponsorship Report
    sr_survival_sponsorship_count = fields.Integer(
        "Number of survival sponsorships",
        compute="_compute_sponsorship_metrics",
        help="Number of survival sponsorships " "for a church AND its members.",
    )

    sr_total_donation_for_csp = fields.Float(
        "Total donation given",
        compute="_compute_sponsorship_metrics",
        help="Total donation given for CSP.",
    )

    sr_nb_moms_supported_for_a_year = fields.Float(
        "Number of moms and babies supported for 1 year (all-in-all)",
        compute="_compute_sponsorship_metrics",
        help="Number of moms and babies supported for a year.",
    )

    sr_countries_current = fields.Char(
        "Countries currently impacted",
        compute="_compute_sponsorship_metrics",
        help="List of current countries impacted "
        "by the church and its members by the CSP program.",
    )

    sr_countries_previous = fields.Char(
        "Countries previously impacted",
        compute="_compute_sponsorship_metrics",
        help="List of previously impacted countries "
        "by the church and its members by the CSP program.",
    )

    def _compute_sponsorship_metrics(self):
        # Early exit for empty recordsets
        if not self:
            return

        """Orchestrator method to calculate and apply all report metrics."""
        # 1. Initialize Default Values
        for partner in self:
            partner.sr_survival_sponsorship_count = 0
            partner.sr_countries_current = ""
            partner.sr_countries_previous = ""
            partner.sr_nb_moms_supported_for_a_year = 0

        # 2. Fetch Data
        annual_cost_baseline = self._get_annual_cost_baseline()
        partner_stats = self._fetch_sponsorship_stats()
        donation_stats = self._fetch_donation_stats()

        # 3. Apply calculated data to records
        for partner in self:
            # Apply Contract/Country Stats
            stats = partner_stats.get(partner.id, {})
            if stats:
                partner.sr_survival_sponsorship_count = stats["count"]
                if stats["current_countries"]:
                    partner.sr_countries_current = ", ".join(
                        sorted(stats["current_countries"])
                    )
                if stats["previous_countries"]:
                    partner.sr_countries_previous = ", ".join(
                        sorted(stats["previous_countries"])
                    )

            # Apply Donation Stats (aggregating members for churches)
            total_donation = donation_stats.get(partner.id, 0.0)
            if partner.is_church:
                total_donation += sum(
                    donation_stats.get(mid, 0.0) for mid in partner.member_ids.ids
                )

            partner.sr_total_donation_for_csp = total_donation

            if annual_cost_baseline > 0:
                partner.sr_nb_moms_supported_for_a_year = round(
                    total_donation / annual_cost_baseline, 2
                )

    def _get_annual_cost_baseline(self):
        """Fetch base annual cost (for CSP only) from product template."""
        survival_tmpl = self.env.ref(
            "survival_sponsorship_compassion.survival_product_template",
            raise_if_not_found=False,
        )
        if not survival_tmpl:
            raise ValueError(
                "Missing required external ID: "
                "'survival_sponsorship_compassion.survival_product_template'. "
                "Ensure the survival product template is installed."
            )

        monthly_cost = survival_tmpl.list_price
        return monthly_cost * 12

    # This function is using raw sql and union all
    # It might seem weird to not use the ORM,
    # but for optimization purposes, raw SQL is better
    # and lighter for the database
    def _fetch_sponsorship_stats(self):
        """Execute raw SQL for contract counts and country sets."""
        churches = self.filtered("is_church")
        query = """
                SELECT rp.id AS partner_id,
                       rc.id AS contract_id,
                       rc.state,
                       rc.csp_country
                FROM res_partner rp
                         LEFT JOIN recurring_contract rc
                                   ON rc.partner_id = rp.id AND rc.type = 'CSP'
                WHERE rp.id IN %s
                UNION ALL
                SELECT p.church_id AS partner_id,
                       rc.id AS contract_id,
                       rc.state,
                       rc.csp_country
                FROM res_partner p
                         JOIN recurring_contract rc
                              ON rc.partner_id = p.id AND rc.type = 'CSP'
                WHERE p.church_id IN %s \
                """
        self.env.cr.execute(
            query, (tuple(self.ids), tuple(churches.ids) if churches else (0,))
        )

        stats = {}
        for row in self.env.cr.dictfetchall():
            pid = row["partner_id"]
            data = stats.setdefault(
                pid,
                {"count": 0, "current_countries": set(), "previous_countries": set()},
            )
            if row["contract_id"]:
                if row["state"] == "active":
                    data["count"] += 1
                    if row["csp_country"]:
                        data["current_countries"].add(row["csp_country"])
                elif row["csp_country"]:
                    data["previous_countries"].add(row["csp_country"])

        # Cleanup: Ensure countries are only in one set
        for data in stats.values():
            data["previous_countries"] -= data["current_countries"]
        return stats

    def _fetch_donation_stats(self):
        """Execute raw SQL for total donation amounts per partner."""
        all_ids = set(self.ids)
        for church in self.filtered("is_church"):
            all_ids.update(church.member_ids.ids)

        query = """
                SELECT am.partner_id,
                       COALESCE(SUM(aml.price_subtotal), 0) AS total_amount
                FROM account_move am
                         JOIN account_move_line aml ON aml.move_id = am.id
                         JOIN recurring_contract rc ON aml.contract_id = rc.id
                WHERE am.partner_id IN %s
                  AND am.move_type = 'out_invoice'
                  AND am.payment_state = 'paid'
                  AND rc.type = 'CSP'
                GROUP BY am.partner_id \
                """
        self.env.cr.execute(query, (tuple(all_ids),))
        return {
            row["partner_id"]: row["total_amount"] for row in self.env.cr.dictfetchall()
        }
