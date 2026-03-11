##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)

try:
    import phonenumbers
except ImportError:
    _logger.error("Please install phonenumbers library")


class CallWizard(models.TransientModel):
    _name = "partner.communication.call.wizard"
    _description = "Partner Communication Call Wizard"

    comments = fields.Text()

    def log_fail(self):
        """Log a failed attempt and close the wizard."""
        self.ensure_one()
        communication_id = self.env.context.get("click2dial_id")
        if communication_id:
            communication = self.env["partner.communication.job"].browse(
                communication_id
            )
            communication.message_post(
                body=_("Phone attempt: ")
                + (self.comments or _("Partner did not answer")),
            )
        self.call_log("cancel")
        return {"type": "ir.actions.act_window_close"}

    def call_success(self):
        """Log a successful call and close the wizard."""
        self.ensure_one()
        self.call_log("done")
        return {"type": "ir.actions.act_window_close"}

    def call_log(self, state):
        """Prepare and create crm.phonecall."""
        communication_id = self.env.context.get("click2dial_id")
        # If no communication ID is in context, we cannot log properly
        if not communication_id:
            return None

        communication = self.env["partner.communication.job"].browse(communication_id)

        call_vals = {
            "state": state,
            "description": self.comments,
            "name": communication.config_id.name or _("Communication Call"),
            "partner_id": communication.partner_id.id,
            "user_id": self.env.uid,
            "date": fields.Datetime.now(),
        }

        # Feedback on the communication activity if successful
        if state == "done" and communication.activity_ids:
            communication.activity_ids.action_feedback(feedback=self.comments)

        # Parse phone number for the crm.phonecall record
        phone_number = self.env.context.get("phone_number")
        if phone_number:
            try:
                parsed_num = phonenumbers.parse(phone_number)
                number_type = phonenumbers.number_type(parsed_num)
                if number_type == 1:
                    call_vals["partner_mobile"] = phone_number
                else:
                    call_vals["partner_phone"] = phone_number
            except (phonenumbers.NumberParseException, TypeError):
                _logger.warning(
                    "Could not parse partner phone number: %s", phone_number
                )
                # Fallback: store it in phone field
                call_vals["partner_phone"] = phone_number

        return self.env["crm.phonecall"].create(call_vals)
