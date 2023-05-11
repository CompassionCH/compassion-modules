##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from dateutil.relativedelta import relativedelta

from odoo import models
from odoo.tools.safe_eval import datetime


class PartnerCommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    def send(self):
        other_jobs = self.filtered(lambda j: j.send_mode != "sms")
        # No money extension
        no_money_1 = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_1"
        )
        settings = self.env["res.config.settings"].sudo()
        first_extension = settings.get_param("no_money_hold_duration")
        for communication in other_jobs:
            extension = False
            if communication.config_id == no_money_1:
                extension = first_extension + 7
            if extension:
                holds = communication.get_objects().mapped("child_id.hold_id")
                for hold in holds:
                    expiration = datetime.now() + relativedelta(days=extension)
                    hold.expiration_date = expiration
