from odoo import _, fields, models


class LogOtherInteractionWizard(models.TransientModel):
    _name = "partner.log.other.interaction.wizard"
    _inherit = "partner.log.other.interaction"
    _description = "Logging wizard for other interactions"
    _transient = True

    ir_attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        readonly=False,
        compute="_compute_attachments",
        inverse="_inverse_ir_attachments",
    )

    def _compute_attachments(self):
        for rec in self:
            rec.ir_attachment_ids = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", rec.id),
                ]
            )

    def _inverse_ir_attachments(self):
        for rec in self:
            rec.ir_attachment_ids.write(
                {
                    "res_model": rec._name,
                    "res_id": rec.id,
                    "res_field": False,
                }
            )

    def log_interaction(self):
        data = {
            "partner_id": self.partner_id.id,
            "subject": self.subject,
            "other_type": self.other_type,
            "communication_type": self.communication_type,
            "direction": self.direction,
            "body": self.body,
            "date": self.date,
        }
        other_interaction = self.env["partner.log.other.interaction"].create(data)
        self.ir_attachment_ids.write(
            {
                "res_model": other_interaction._name,
                "res_id": other_interaction.id,
                "res_field": False,
            }
        )
        self.partner_id.fetch_interactions()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("The interaction has been added to the resume."),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
