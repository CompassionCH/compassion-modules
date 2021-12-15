from odoo import models, api, fields


class LogOtherInteractionWizard(models.TransientModel):
    _name = "partner.log.other.interaction.wizard"
    _description = "Logging wizard for other interactions"

    partner_id = fields.Many2one("res.partner", "Partner", default=lambda self: self.env.context.get("active_id"), readonly=False)
    subject = fields.Char()
    other_type = fields.Char()
    direction = fields.Selection([("in", "Incoming"), ("out", "Outgoing"), ])
    body = fields.Html()

    def log_interaction(self):
        data = {
            "partner_id": self.partner_id.id,
            "subject": self.subject,
            "other_type": self.other_type,
            "direction": self.direction,
            "body": self.body,
        }
        self.env["partner.log.other.interaction"].create(data)


class OtherInteractions(models.Model):
    _name = "partner.log.other.interaction"
    _description = "Logging for other interactions"

    partner_id = fields.Many2one("res.partner")
    subject = fields.Char()
    other_type = fields.Char()
    direction = fields.Selection([("in", "Incoming"), ("out", "Outgoing"), ])
    body = fields.Html()
