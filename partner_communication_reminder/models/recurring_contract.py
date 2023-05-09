##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    @api.model
    def create_reminder_communication(self):
        _logger.info("Creating Sponsorship Reminders")
        search_domain = [
            ("state", "in", ("active", "mandate")),
            ("global_id", "!=", False),
            ("type", "like", "S"),
            "|",
            ("child_id.project_id.suspension", "!=", "fund-suspended"),
            ("child_id.project_id.suspension", "=", False),
            ("months_due", ">", 1)
        ]
        first_reminder_config = self.env.ref(
            "partner_communication_reminder.sponsorship_reminder_1"
        )
        first_reminder = self.search(search_domain).with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )
        first_reminder.send_communication(
            first_reminder_config, correspondent=False
        )
        _logger.info("Sponsorship Reminders created!")
        return True
