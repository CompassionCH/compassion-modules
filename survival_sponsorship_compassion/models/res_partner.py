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

        # 1. Extract just the churches from the batch
        churches = self.filtered("is_church")

        # 2. Branch the queries safely based on whether churches are present in the batch
        if churches:
            query = """
                    SELECT rp.id AS partner_id, COUNT(rc.id) AS active_csp_contracts_count
                    FROM res_partner rp
                             LEFT JOIN recurring_contract rc ON rc.partner_id = rp.id
                        AND rc.type = 'CSP' AND rc.state = 'active'
                    WHERE rp.id IN %s
                    GROUP BY rp.id

                    UNION ALL

                    SELECT p.church_id AS partner_id, COUNT(rc.id) AS active_csp_contracts_count
                    FROM res_partner p
                             JOIN recurring_contract rc ON rc.partner_id = p.id
                        AND rc.type = 'CSP' AND rc.state = 'active'
                    WHERE p.church_id IN %s
                    GROUP BY p.church_id \
                    """
            self.env.cr.execute(query, (tuple(self.ids), tuple(churches.ids)))

            # Since UNION ALL can return two rows for a church, aggregate them here
            res_dict = {}
            for row in self.env.cr.dictfetchall():
                pid = row["partner_id"]
                res_dict[pid] = res_dict.get(pid, 0) + row["active_csp_contracts_count"]

        else:
            # 3. Ultra-optimized query for regular partners (like standard form views)
            # We completely cut out the middleman join on res_partner 'p'
            query = """
                    SELECT rp.id AS partner_id, COUNT(rc.id) AS active_csp_contracts_count
                    FROM res_partner rp
                    LEFT JOIN recurring_contract rc ON rc.partner_id = rp.id
                        AND rc.type = 'CSP'
                        AND rc.state = 'active'
                    WHERE rp.id IN %s
                    GROUP BY rp.id \
                    """
            self.env.cr.execute(query, (tuple(self.ids),))
            res_dict = {row["partner_id"]: row["active_csp_contracts_count"] for row in self.env.cr.dictfetchall()}

        # 4. Assign the values back safely
        for partner in self:
            partner.survival_sponsorship_count = res_dict.get(partner.id, 0)

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

        # 1. Fetch exact contract IDs using raw SQL.
        # This bypasses Odoo's slow ORM domain expansion and targets indexes directly.
        query = """
                SELECT rc.id
                FROM recurring_contract rc
                         JOIN res_partner p ON rc.partner_id = p.id
                WHERE rc.type = 'CSP'
                  AND rc.state = 'active'
                  AND (p.id = %s OR p.church_id = %s) \
                """
        self.env.cr.execute(query, (self.id, self.id))

        # Extract a clean, lightweight list of integer IDs
        contract_ids = [row[0] for row in self.env.cr.fetchall()]

        # 2. Build a super lightweight domain using the explicit IDs.
        # If no contracts are found, use a fast failing domain [('id', '=', False)]
        domain = [("id", "in", contract_ids)] if contract_ids else [("id", "=", False)]

        return {
            "name": _("Survival Sponsorships"),
            "type": "ir.actions.act_window",
            "res_model": "recurring.contract",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {
                "default_type": "CSP",
                "default_state": "active",
                "default_partner_id": self.id,
            },
            "target": "current",
        }