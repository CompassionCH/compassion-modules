from odoo import fields, models


class IrLogging(models.Model):
    _inherit = 'ir.logging'
    context_data = fields.Text("Additional data")
