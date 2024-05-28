from odoo import fields, models


class CompassionProject(models.Model):
    """Send Communication when Hold Removal is received."""

    _inherit = "compassion.project"

    tpl_item_ids = fields.Many2many(
        "communication.snippet",
        "name",
        "snippet_text",
        string="Caption to use for pictures, or prayer shared by fcp, or else",
    )
