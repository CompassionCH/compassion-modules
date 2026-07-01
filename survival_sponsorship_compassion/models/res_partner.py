from odoo import _, fields, models


# For more readability we have split "res.partner" by functionality
# pylint: disable=R8180
class ResPartner(models.Model):
    _inherit = "res.partner"

    survival_sponsorship_count = fields.Integer(
        string="Survival sponsorship(s)",
        compute="_compute_active_csp_count",
    )

    def _get_survival_sponsorship_data(self):
        churches = self.filtered("is_church")
        all_ids = set(self.ids)
        church_member_map = {c.id: c.member_ids.ids for c in churches}
        for members in church_member_map.values():
            all_ids.update(members)

        group_data = self.env["recurring.contract"].read_group(
            domain=[("partner_id", "in", list(all_ids)), ("type", "=", "CSP")],
            fields=["partner_id", "state", "csp_country"],
            groupby=["partner_id", "state", "csp_country"],
            lazy=False,
        )

        results = {
            pid: {"active_count": 0, "curr": set(), "prev": set()} for pid in all_ids
        }

        for row in group_data:
            pid = row["partner_id"][0]
            if pid not in results:
                continue
            if row["state"] == "active":
                results[pid]["active_count"] += row["__count"]
                if row["csp_country"]:
                    results[pid]["curr"].add(row["csp_country"])
            elif row["csp_country"]:
                results[pid]["prev"].add(row["csp_country"])

        return results, church_member_map

    def _compute_active_csp_count(self):
        data, member_map = self._get_survival_sponsorship_data()
        for partner in self:
            count = data.get(partner.id, {}).get("active_count", 0)
            if partner.is_church:
                count += sum(
                    data.get(mid, {}).get("active_count", 0)
                    for mid in member_map.get(partner.id, [])
                )
            partner.survival_sponsorship_count = count

    def open_survival_sponsorships(self):
        self.ensure_one()
        return {
            "name": _("Survival Sponsorships"),
            "type": "ir.actions.act_window",
            "res_model": "recurring.contract",
            "view_mode": "list,form",
            "domain": [
                ("type", "=", "CSP"),
                ("state", "=", "active"),
                "|",
                ("partner_id", "=", self.id),
                ("partner_id.church_id", "=", self.id),
            ],
            "context": {
                "create": False,
                "default_type": "CSP",
                "default_partner_id": self.id,
            },
            "target": "current",
        }

    def _compute_related_contracts(self):
        res = super()._compute_related_contracts()
        contract_obj = self.env["recurring.contract"]
        for partner in self:
            partner.contracts_correspondant += contract_obj.search(
                [
                    ("correspondent_id", "=", partner.id),
                    ("type", "=", "CSP"),
                    ("fully_managed", "=", False),
                ],
                order="start_date desc",
            )
            partner.contracts_paid += contract_obj.search(
                [
                    ("partner_id", "=", partner.id),
                    ("type", "=", "CSP"),
                    ("fully_managed", "=", False),
                ],
                order="start_date desc",
            )
            partner.contracts_fully_managed += contract_obj.search(
                [
                    ("partner_id", "=", partner.id),
                    ("type", "=", "CSP"),
                    ("fully_managed", "=", True),
                ],
                order="start_date desc",
            )
            partner.other_contract_ids = partner.other_contract_ids.filtered(
                lambda c: c.type != "CSP"
            )
        return res
