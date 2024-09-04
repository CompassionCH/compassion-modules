from odoo import fields, models
from odoo.tools import html2plaintext


class OtherInteractions(models.Model):
    _name = "partner.log.other.interaction"
    _inherit = [
        "mail.activity.mixin",
        "mail.thread",
        "interaction.source",
    ]
    _description = "Logging for other interactions"
    _rec_name = "subject"

    partner_id = fields.Many2one(
        "res.partner", "Partner", default=lambda self: self.env.context.get("active_id")
    )
    subject = fields.Char(required=True)
    communication_type = fields.Selection(
        [
            ("Paper", "Paper"),
            ("Phone", "Phone"),
            ("SMS", "SMS"),
            ("Email", "Email"),
            ("Mass", "Mass Mailing"),
            ("Other", "Other"),
            ("Support", "Support"),
        ],
        required=True,
    )
    other_type = fields.Char()
    date = fields.Datetime(default=fields.Datetime.now)
    direction = fields.Selection(
        [("in", "Incoming"), ("out", "Outgoing")], required=True
    )
    body = fields.Html()

    def _get_interaction_data(self, partner_id):
        return [
            {
                "partner_id": partner_id,
                "res_model": self._name,
                "res_id": rec.id,
                "direction": rec.direction,
                "date": rec.date,
                "communication_type": rec.communication_type,
                "body": html2plaintext(rec.body).replace("\n\n", "\n"),
                "subject": rec.subject,
                "other_type": rec.other_type,
            }
            for rec in self
        ]

    def write(self, vals):
        res = super().write(vals)
        # Refresh interaction resume
        interaction = self.env["interaction.resume"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )
        interaction.unlink()
        self.mapped("partner_id").fetch_interactions()
        return res
