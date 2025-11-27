##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class ResPartnerMatch(models.AbstractModel):
    _inherit = "res.partner.match"

    @api.model
    def _match_email(self, vals):
        # Redefine email rule to include aliases in search
        # and exclude Compassion addresses
        email = vals["email"].strip()
        partner = self.env["res.partner"].search(
            [
                ("email", "not like", "compassion"),
                "|",
                "|",
                ("email", "=ilike", email),
                ("email_alias_ids.email", "=ilike", email),
                ("other_contact_ids.email", "=ilike", email),
            ]
        )
        return partner
