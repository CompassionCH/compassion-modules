from odoo import _, models


class LogOtherInteractionWizard(models.TransientModel):
    _name = "partner.log.other.interaction.wizard"
    _inherit = "partner.log.other.interaction"
    _description = "Logging wizard for other interactions"
    _transient = True

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
        # used str.format for concatenating other_interaction.subject and
        # other_interaction.other_type within the anchor tag's display text
        # dynamic content is formatted into the string after it's been prepared
        # for translation
        message_template = (
            "Your new interaction has been created! Click the link to access it: "
            "<a href=# data-oe-model={} data-oe-id={}>{}</a>"
        )
        formatted_message = message_template.format(
            other_interaction._name,
            other_interaction.id,
            "{} {}".format(other_interaction.subject, other_interaction.other_type),
        )
        message = self.partner_id.message_post(body=_(formatted_message))
        # Only keep the note within one minute
        message.with_delay(eta=60).unlink()
        self.partner_id.fetch_interactions()
        return True
