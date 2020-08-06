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

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

try:
    import phonenumbers
except ImportError:
    _logger.error("Please install phonenumbers")


class CallWizard(models.TransientModel):
    _name = "partner.communication.call.wizard"
    _description = "Partner Communication Call Wizard"

    comments = fields.Text()

    @api.multi
    def log_fail(self):
        state = "cancel"
        communication = self.env["partner.communication.job"].browse(
            self.env.context.get("click2dial_id")
        )
        communication.message_post(
            body=_("Phone attempt: ") + (self.comments or _("Partner did not answer")),
        )
        return self.call_log(state)

    @api.multi
    def call_success(self):
        state = "done"
        return self.call_log(state)

    @api.multi
    def call_log(self, state):
        """ Prepare crm.phonecall creation. """
        communication_id = self.env.context.get("click2dial_id")
        communication = self.env["partner.communication.job"].browse(communication_id)
        call_vals = {
            "state": state,
            "description": self.comments,
            "name": communication.config_id.name,
            "communication_id": communication_id,
            "partner_id": communication.partner_id.id,
        }
        if state == "done":
            communication.activity_ids.action_feedback(self.comments)
        try:
            parsed_num = phonenumbers.parse(self.env.context.get("phone_number"))
            number_type = phonenumbers.number_type(parsed_num)
            if number_type == 1:
                call_vals["partner_mobile"] = self.env.context.get("phone_number")
            else:
                call_vals["partner_phone"] = self.env.context.get("phone_number")
        except TypeError:
            _logger.info("Partner has no phone number")
        return self.env["crm.phonecall"].create(call_vals)
