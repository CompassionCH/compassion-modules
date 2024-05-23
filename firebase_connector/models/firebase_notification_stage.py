from odoo import fields, models


class FirebaseNotificationStage(models.Model):
    _name = "firebase.notification.stage"
    _description = "Notification stages"
    _order = "sequence"

    name = fields.Char(
        string="Stage Name",
        required=True,
        translate=True,
    )
    sequence = fields.Integer(
        default=10,
        help="Used to order stages. Lower is better.",
    )

    active = fields.Boolean(default=True)
