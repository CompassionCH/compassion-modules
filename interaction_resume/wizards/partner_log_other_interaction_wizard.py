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
        # Copy the attachments to persist them
        for attachment in self.ir_attachment_ids:
            self.env["ir.attachment"].create(
                {
                    "res_model": self._name,
                    "res_id": self.id,
                    "name": attachment.name,
                    "datas": attachment.datas,
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
        # used str.format for concatenating other_interaction.subject and
        # other_interaction.other_type within the anchor tag's display text
        # dynamic content is formatted into the string after it's been prepared
        # for translation
        message_template = _(
            "Your new interaction has been created! Click the link to access it: "
            "<a href=# data-oe-model='{model}' data-oe-id='{res_id}'>{name}</a>"
        )
        link_name = (
            f"{other_interaction.subject} {other_interaction.other_type or ''}".strip()
        )
        formatted_message = message_template.format(
            model=other_interaction._name,
            res_id=other_interaction.id,
            name=link_name,
        )
        message = self.partner_id.message_post(body=formatted_message)
        # Only keep the note within one minute
        message.with_delay_sh(
            "unlink",
            channel="root.partner_communication",
            eta=60,
            priority=500,
            description="Delete new interaction log after 1 minute",
        )
        self.partner_id.fetch_interactions()
        return True
