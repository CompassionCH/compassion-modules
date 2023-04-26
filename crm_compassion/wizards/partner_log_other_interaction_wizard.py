from odoo import models, fields


class LogOtherInteractionWizard(models.TransientModel):
    _name = "partner.log.other.interaction.wizard"
    _description = "Logging wizard for other interactions"

    partner_id = fields.Many2one(
        "res.partner", "Partner", default=lambda self: self.env.context.get("active_id")
    )
    subject = fields.Char(required=True)
    other_type = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    direction = fields.Selection(
        [("in", "Incoming"), ("out", "Outgoing")], required=True
    )
    body = fields.Html()

    def log_interaction(self):
        data = {
            "partner_id": self.partner_id.id,
            "subject": self.subject,
            "other_type": self.other_type,
            "direction": self.direction,
            "body": self.body,
            "date": self.date,
        }
        other_interaction = self.env["partner.log.other.interaction"].create(data)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'New interaction created',
                'message': "Your new interaction has been created! Click the link to access it: "
                           f"<a href='web#id={other_interaction.id}&view_type=form&model=mail.mail'>{other_interaction.subject}</a>",
                'sticky': True,
            }
        }

class OtherInteractions(models.Model):
    _name = "partner.log.other.interaction"
    _inherit = [
        "mail.activity.mixin",
        "mail.thread",
        "partner.log.other.interaction.wizard",
    ]
    _description = "Logging for other interactions"
    _rec_name = "subject"
    _transient = False
