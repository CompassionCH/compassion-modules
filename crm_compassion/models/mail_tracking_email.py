from odoo import fields, models


# Adds a few indexes for performance of interaction resume
class MailTrackingEmail(models.Model):
    _inherit = "mail.tracking.email"

    mail_id = fields.Many2one(index=True)


class MailMessage(models.Model):
    _inherit = "mail.message"

    message_type = fields.Selection(index=True)
    subject = fields.Char(index=True)
