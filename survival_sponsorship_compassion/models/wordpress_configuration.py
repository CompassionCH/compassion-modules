from odoo import fields, models


class WordpressConfiguration(models.Model):
    _inherit = "wordpress.configuration"

    survival_sponsorship_url = fields.Char(translate=True)
