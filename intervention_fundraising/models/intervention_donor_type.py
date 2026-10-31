from odoo import fields, models


class InterventionDonorType(models.Model):
    _name = "intervention.donor.type"
    _description = "Donor type suited to an intervention"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
