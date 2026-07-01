##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models


# For more readability we have split "res.partner" by functionality
# pylint: disable=R7980
class PartnerSponsorshipReport(models.Model):
    _inherit = "res.partner"

    sr_survival_sponsorship_count = fields.Integer(
        "Number of survival sponsorships",
        compute="_compute_sponsorship_metrics",
        help="Number of survival sponsorships for a church AND its members.",
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
        help="List of current countries impacted by the church and its members "
        "by the CSP program.",
    )
    sr_countries_previous = fields.Char(
        "Countries previously impacted",
        compute="_compute_sponsorship_metrics",
        help="List of previously impacted countries by the church and its members "
        "by the CSP program.",
    )

    def _compute_sponsorship_metrics(self):
        """Orchestrator method to calculate and apply all report metrics."""
        if not self:
            return

        for partner in self:
            partner.sr_survival_sponsorship_count = 0
            partner.sr_total_donation_for_csp = 0.0
            partner.sr_countries_current = ""
            partner.sr_countries_previous = ""
            partner.sr_nb_moms_supported_for_a_year = 0

        annual_cost_baseline = self._get_annual_cost_baseline()
        partner_stats = self._fetch_sponsorship_stats()
        donation_stats = self._fetch_donation_stats()

        for partner in self:
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
        """Fetch base annual cost (CSP only) from the survival product template."""
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
        return survival_tmpl.list_price * 12

    def _fetch_sponsorship_stats(self):
        """Execute raw SQL for contract counts and country sets."""
        churches = self.filtered("is_church")
        self.env.cr.execute(
            """
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
            WHERE p.church_id IN %s
            """,
            (tuple(self.ids), tuple(churches.ids) if churches else (0,)),
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

        for data in stats.values():
            data["previous_countries"] -= data["current_countries"]
        return stats

    def _fetch_donation_stats(self):
        """Execute raw SQL for total CSP donation amounts per partner."""
        all_ids = set(self.ids)
        for church in self.filtered("is_church"):
            all_ids.update(church.member_ids.ids)

        self.env.cr.execute(
            """
            SELECT am.partner_id,
                   COALESCE(SUM(aml.price_subtotal), 0) AS total_amount
            FROM account_move am
                     JOIN account_move_line aml ON aml.move_id = am.id
                     JOIN recurring_contract rc ON aml.contract_id = rc.id
            WHERE am.partner_id IN %s
              AND am.move_type = 'out_invoice'
              AND am.payment_state = 'paid'
              AND rc.type = 'CSP'
            GROUP BY am.partner_id
            """,
            (tuple(all_ids),),
        )
        return {
            row["partner_id"]: row["total_amount"] for row in self.env.cr.dictfetchall()
        }
