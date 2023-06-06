##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class RecurringContractGroup(models.Model):
    _inherit = "recurring.contract.group"

    @api.multi
    def _compute_contains_sponsorship(self):
        super()._compute_contains_sponsorship()
        for group in self:
            sponsorships = group.mapped("contract_ids").filtered(
                lambda s: s.type == "CSP" and s.state not in (
                    "terminated", "cancelled")
            )
            if sponsorships:
                group.contains_sponsorship = True
