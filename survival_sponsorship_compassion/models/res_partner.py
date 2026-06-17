##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    survival_sponsorship_count = fields.Integer(
        string="Survival sponsorship(s)",
        compute="_compute_active_csp_count",
        store=False,  # Not stored in the database, computed on the fly
        copy=False,
    )

    def _compute_active_csp_count(self):
        if not self:
            return

        churches = self.filtered("is_church")
        partner_ids = self.ids
        if churches:
            partner_ids = list(set(partner_ids + churches.member_ids.ids))

        contracts = self.env["recurring.contract"].search([
            ("partner_id", "in", partner_ids),
            ("type", "=", "CSP"),
            ("state", "=", "active"),
        ])

        contract_counts = {}
        for contract in contracts:
            pid = contract.partner_id.id
            contract_counts[pid] = contract_counts.get(pid, 0) + 1

        for partner in self:
            count = contract_counts.get(partner.id, 0)
            if partner.is_church:
                count += sum(contract_counts.get(mid, 0) for mid in partner.member_ids.ids)
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
                "default_type": "CSP",
                "default_state": "active",
                "default_partner_id": self.id,
            },
            "target": "current",
        }
