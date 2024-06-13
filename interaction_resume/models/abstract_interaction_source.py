from odoo import api, fields, models


class InteractionSource(models.AbstractModel):
    _name = "interaction.source"

    # Just making sure the fields exist in the model
    partner_id = fields.Many2one("res.partner")
    date = fields.Datetime()

    @api.model
    def fetch_interaction(
        self,
        partner,
        since=None,
        until=None,
    ):
        """
        Create interaction records for a given partner and date range
        @param partner:
        @param since:
        @param until:
        """
        search_domain = self._get_interaction_partner_domain(partner)
        records = self.search(
            [
                *search_domain,
                ("date", ">=", since),
                ("date", "<=", until),
            ]
        )
        self.env["interaction.resume"].create(records._get_interaction_data(partner.id))
        return True

    def _get_interaction_partner_domain(self, partner):
        return [
            "|",
            "|",
            ("partner_id", "=", partner.id),
            ("partner_id.email", "=", partner.email),
            ("partner_id", "in", partner.other_contact_ids.ids),
        ]

    def _get_interaction_data(self, partner_id):
        return [
            {
                "partner_id": partner_id,
                "res_model": self._name,
                "res_id": rec.id,
            }
            for rec in self
        ]

    def create(self, vals_list):
        res = super().create(vals_list)
        # Invalidate partner last interaction date
        res.mapped("partner_id").write({"last_interaction_fetch_date": False})
        return res
