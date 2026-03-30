from odoo import fields, models


class CorrespondenceParagraph(models.Model):
    _inherit = "correspondence.paragraph"

    comments = fields.Text()
