##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


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
