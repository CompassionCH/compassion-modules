from odoo import models


class CompassionHold(models.Model):
    _inherit = "compassion.hold"

    def postpone_no_money_hold(self, additional_text=None):
        """
        Send a communication to sponsor for reminding the payment.
        :param additional_text: text to add in the notification to hold owner
        :return: None
        """
        first_reminder_config = self.env.ref(
            "partner_communication_reminder.sponsorship_waiting_reminder_1"
        )
        # Check communications already pending and put them back to their state
        first_reminders = self.env["partner.communication.job"].search([
            ("config_id", "=", first_reminder_config.id),
            ("state", "=", "pending")
        ])
        if first_reminders:
            first_pending_holds = first_reminders.get_objects().mapped(
                "child_id.hold_id")
            (first_pending_holds & self).write({"no_money_extension": 0})
        super().postpone_no_money_hold(additional_text)
