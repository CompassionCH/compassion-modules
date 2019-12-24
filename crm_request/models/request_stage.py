# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RequestStage(models.Model):
    _inherit = "crm.claim.stage"

    active = fields.Boolean(default=True)
