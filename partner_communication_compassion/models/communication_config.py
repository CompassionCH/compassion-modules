##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class CommunicationConfig(models.Model):
    _inherit = "partner.communication.config"

    @api.model_create_multi
    def create(self, vals_list):
        # A communication is the source of what it brings: a mailing
        for vals in vals_list:
            vals.setdefault("category", "mailing")
        return super().create(vals_list)
