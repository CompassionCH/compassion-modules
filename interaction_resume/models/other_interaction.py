from odoo import models
from odoo.tools import html2plaintext


class OtherInteractions(models.Model):
    _name = "partner.log.other.interaction"
    _inherit = [
        "mail.activity.mixin",
        "mail.thread",
        "partner.log.other.interaction.wizard",
        "interaction.source",
    ]
    _description = "Logging for other interactions"
    _rec_name = "subject"
    _transient = False

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
