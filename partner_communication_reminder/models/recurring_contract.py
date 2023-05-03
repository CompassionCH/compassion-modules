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
    def send_sponsorship_reminders(self):
        _logger.info("Creating Sponsorship Reminders")
        today = datetime.now()
        first_day_of_month = date(today.year, today.month, 1)
        first_reminder_config = self.env.ref(
            "partner_communication_reminder.sponsorship_reminder_1"
        )
        second_reminder_config = self.env.ref(
            "partner_communication_reminder.sponsorship_reminder_2"
        )
        first_reminder = self.with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )
        second_reminder = self.with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )
        twenty_ago = today - relativedelta(days=20)
        comm_obj = self.env["partner.communication.job"]
        search_domain = [
            ("state", "in", ("active", "mandate")),
            ("global_id", "!=", False),
            ("type", "like", "S"),
            "|",
            ("child_id.project_id.suspension", "!=", "fund-suspended"),
            ("child_id.project_id.suspension", "=", False),
        ]

        for sponsorship in self.search(
                search_domain + [("months_due", ">", 1)]):
            reminder_search = [
                (
                    "config_id",
                    "in",
                    [first_reminder_config.id, second_reminder_config.id],
                ),
                ("state", "=", "done"),
                ("object_ids", "like", str(sponsorship.id)),
            ]
            # Look if first reminder was sent previous month (send second
            # reminder in that case)
            # avoid taking into account reminder that the partner already took care of
            # we substract month due to the first of the month to get the older threshold
            # this also prevent reminder_1 to be sent after an already sent reminder_2
            older_threshold = first_day_of_month - relativedelta(months=sponsorship.months_due)

            has_first_reminder = comm_obj.search_count(
                reminder_search
                + [("sent_date", ">=", older_threshold),
                   ("sent_date", "<", twenty_ago)]
            )
            if has_first_reminder:
                second_reminder += sponsorship
            else:
                # Send first reminder only if one was not already sent less
                # than twenty days ago
                has_first_reminder = comm_obj.search_count(
                    reminder_search + [("sent_date", ">=", twenty_ago)]
                )
                if not has_first_reminder:
                    first_reminder += sponsorship
        first_reminder.send_communication(
            first_reminder_config, correspondent=False)
        second_reminder.send_communication(
            second_reminder_config, correspondent=False)
        _logger.info("Sponsorship Reminders created!")
        return True
