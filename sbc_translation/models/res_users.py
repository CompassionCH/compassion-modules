from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    translated_letter_ids = fields.One2many(
        "correspondence", "user_id", "Translated letters", readonly=False
    )
