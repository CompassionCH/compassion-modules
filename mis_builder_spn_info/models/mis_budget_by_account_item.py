# Copyright 2024-today Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisBudgetByAccountItem(models.Model):
    _inherit = "mis.budget.by.account.item"

    product_id = fields.Many2one("product.product")
