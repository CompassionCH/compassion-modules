from odoo import models, fields


class CorrespondenceParagraph(models.Model):
    _inherit = "correspondence.paragraph"

    comments = fields.Text()
