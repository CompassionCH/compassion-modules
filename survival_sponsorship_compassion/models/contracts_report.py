from dateutil.relativedelta import relativedelta

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

    sr_nb_moms_supported_for_a_year = fields.Integer(
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
        # 1. Default initialization for all batch records
        for partner in self:
            partner.sr_survival_sponsorship_count = 0
            partner.sr_countries_current = ""
            partner.sr_countries_previous = ""
            partner.sr_nb_moms_supported_for_a_year = 0

        # DYNAMIC PRICING LOOKUP: Fetch the base monthly value from the template config
        # If the template or price isn't initialized yet, safe-fallback to 62.0
        survival_tmpl = self.env.ref(
            "survival_sponsorship_compassion.survival_product_template",
            raise_if_not_found=False,
        )
        monthly_cost = (survival_tmpl.list_price or 62.0) if survival_tmpl else 62.0
        annual_cost_baseline = monthly_cost * 12

        churches = self.filtered("is_church")
        partner_ids = tuple(self.ids)

        # 2. Unified Query Execution Path
        if churches:
            query = """
                    SELECT rp.id AS partner_id,
                           rc.id AS contract_id,
                           rc.state, rc.csp_country
                    FROM res_partner rp
                             LEFT JOIN recurring_contract rc
                                       ON rc.partner_id = rp.id AND rc.type = 'CSP'
                    WHERE rp.id IN %s

                    UNION ALL

                    SELECT p.church_id AS partner_id,
                           rc.id AS contract_id,
                           rc.state, rc.csp_country
                    FROM res_partner p
                             JOIN recurring_contract rc
                                  ON rc.partner_id = p.id AND rc.type = 'CSP'
                    WHERE p.church_id IN %s
                    """
            self.env.cr.execute(query, (partner_ids, tuple(churches.ids)))
        else:
            query = """
                    SELECT rp.id AS partner_id,
                           rc.id AS contract_id,
                           rc.state,
                           rc.csp_country
                    FROM res_partner rp
                             LEFT JOIN recurring_contract rc
                                       ON rc.partner_id = rp.id AND rc.type = 'CSP'
                    WHERE rp.id IN %s \
                    """
            self.env.cr.execute(query, (partner_ids,))

        # 3. Aggregate both datasets simultaneously with conditional logic
        partner_data = {}
        for row in self.env.cr.dictfetchall():
            pid = row["partner_id"]
            cid = row["contract_id"]
            state = row["state"]
            country = row["csp_country"]

            stats = partner_data.setdefault(
                pid,
                {"count": 0, "current_countries": set(), "previous_countries": set()},
            )

            if cid:
                # Condition A: Only increment the counter if the contract is active
                if state == "active":
                    stats["count"] += 1
                    if country:
                        stats["current_countries"].add(country)

                # Condition B: Collect the country
                # regardless of what the contract state is
                else:
                    if country:
                        stats["previous_countries"].add(country)

        # 4. Batched & Optimized Query for Donations (Moms Supported)
        # Collect all unique target IDs (partners + their church members)
        today = fields.Date.today()
        start_date = today - relativedelta(months=12)

        all_donation_partner_ids = set(self.ids)
        for church in churches:
            if church.member_ids:
                all_donation_partner_ids.update(church.member_ids.ids)

        donation_data = {}
        if all_donation_partner_ids:
            # We join account_move with res_partner to dynamically validate
            # each record against its own start_period and end_period in a single sweep
            # See the sponsorship_compassion.contracts_reports file for similar behavior
            donation_query = """
                            SELECT am.partner_id, 
                                   COALESCE(SUM(aml.price_subtotal), 0) AS total_amount
                            FROM account_move am
                            JOIN account_move_line aml ON aml.move_id = am.id
                            JOIN recurring_contract rc ON aml.contract_id = rc.id
                            WHERE am.partner_id IN %s
                              AND am.move_type = 'out_invoice'
                              AND am.payment_state = 'paid'
                              AND rc.type = 'CSP'
                              AND am.last_payment < %s
                              AND am.last_payment > %s
                            GROUP BY am.partner_id
                             """
            self.env.cr.execute(
                donation_query, (tuple(all_donation_partner_ids), today, start_date)
            )
            donation_data = {
                row["partner_id"]: row["total_amount"]
                for row in self.env.cr.dictfetchall()
            }

        # 5. Write back values to the Odoo recordset cache cleanly
        for partner in self:
            data = partner_data.get(partner.id)
            if data:
                partner.sr_survival_sponsorship_count = data["count"]

                current_set = data["current_countries"]
                previous_set = data["previous_countries"] - current_set
                if current_set:
                    partner.sr_countries_current = ", ".join(sorted(current_set))
                if previous_set:
                    partner.sr_countries_previous = ", ".join(sorted(previous_set))

            # Accumulate and write donation metrics
            total_donation = donation_data.get(partner.id, 0.0)
            if partner.is_church:
                total_donation += sum(
                    donation_data.get(mid, 0.0) for mid in partner.member_ids.ids
                )

            # Divide total by annual_cost_baseline
            # (monthly_cost * 12, where monthly_cost is read from
            # the product template, defaulting to 62.0)
            partner.sr_nb_moms_supported_for_a_year = int(
                total_donation / annual_cost_baseline
            )
