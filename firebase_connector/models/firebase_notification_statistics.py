from odoo import fields, models


class FirebaseNotificationStatistics(models.Model):
    _name = "firebase.notification.statistics"
    _description = "Notification statistics"

    notification_id = fields.Many2one(
        "firebase.notification",
        "Notification",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=False,
    )
    code = fields.Char()
    delivered = fields.Boolean(default=False)
    failed = fields.Boolean(default=False)
    create_date = fields.Datetime()
    registration_id = fields.Many2one(
        "firebase.registration",
        "Registration",
        ondelete="cascade",
        index=True,
        readonly=False,
    )
    partner_name = fields.Char(
        string="Partner",
        store=True,
        related="registration_id.partner_id.name",
        readonly=True,
    )
