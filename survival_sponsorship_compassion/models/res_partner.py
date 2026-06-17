from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    survival_sponsorship_count = fields.Integer(
        string="Survival sponsorship(s)",
        compute="_compute_active_csp_count",
    )

    def _compute_active_csp_count(self):
        churches = self.filtered("is_church")
        all_partner_ids = set(self.ids)
        if churches:
            all_partner_ids.update(churches.mapped("member_ids.id"))

        group_data = self.env["recurring.contract"].read_group(
            domain=[
                ("partner_id", "in", list(all_partner_ids)),
                ("type", "=", "CSP"),
                ("state", "=", "active"),
            ],
            fields=["partner_id"],
            groupby=["partner_id"],
        )

        contract_counts = {
            item["partner_id"][0]: item["partner_id_count"] for item in group_data
        }

        # Assign counts to each partner
        for partner in self:
            count = contract_counts.get(partner.id, 0)
            if partner.is_church:
                # Add counts for all associated members
                count += sum(contract_counts.get(m.id, 0) for m in partner.member_ids)
            partner.survival_sponsorship_count = count

    def _compute_related_contracts(self):
        super()._compute_related_contracts()
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

    def open_survival_sponsorships(self):
        self.ensure_one()

        return {
            "name": _("Survival Sponsorships"),
            "type": "ir.actions.act_window",
            "res_model": "recurring.contract",
            "view_mode": "tree,form",
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
