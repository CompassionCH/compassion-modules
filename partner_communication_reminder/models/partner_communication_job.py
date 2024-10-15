##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models


class PartnerCommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    def send(self):
        settings = self.env["res.config.settings"].sudo()
        first_extension = settings.get_param("no_money_hold_duration")
        second_extension = settings.get_param("no_money_hold_extension")
        extension_mapping = {
            self.env.ref(
                "partner_communication_reminder.sponsorship_activation_reminder_1"
            ): first_extension + 7,
            self.env.ref(
                "partner_communication_reminder.sponsorship_activation_reminder_2"
            ): second_extension + 7,
            self.env.ref(
                "partner_communication_reminder.sponsorship_activation_reminder_3"
            ): 10,
        }
        for communication in self.filtered(lambda j: j.send_mode != "sms"):
            config_id = communication.config_id
            extension = extension_mapping.get(config_id)
            if extension:
                holds = communication.get_objects().mapped("child_id.hold_id")
                expiration = datetime.now() + relativedelta(days=extension)
                holds.write({"expiration_date": expiration})
        return super().send()
