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
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    _inherit = "recurring.contract"

    def contract_active(self):
        """Remove waiting reminders if any"""
        self.env["partner.communication.job"].search(
            [
                ("config_id.name", "ilike", "Waiting reminder"),
                ("state", "!=", "done"),
                ("partner_id", "in", self.mapped("partner_id").ids),
            ]
        ).unlink()
        super().contract_active()
        return True

    def _get_custom_context_for_reminder(self):
        return self.with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )

    @api.model
    def create_reminder_communication(self):
        """Creation of the reminder for active and waiting contracts"""
        _logger.info("Creating Sponsorship Reminders")
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        reminder_conf_list = self.env["partner.communication.config"]
        for i in range(1, 4):
            reminder_conf_list += self.env.ref(
                f"partner_communication_reminder.sponsorship_reminder_{i}"
            )
        twenty_days_ago = today - relativedelta(days=20)
        partnerCommunicationJob = self.env["partner.communication.job"]
        search_domain = [
            ("months_due", ">", 1),
            ("state", "in", ("active", "mandate")),
            ("gmc_commitment_id", "!=", False),
            ("type", "like", "S"),
            "|",
            ("child_id.project_id.suspension", "!=", "fund-suspended"),
            ("child_id.project_id.suspension", "=", False),
        ]
        contracts_eligible_reminder_dict = {
            "first": self.env[(self._name)],
            "second": self.env[(self._name)],
            "third": self.env[(self._name)],
        }
        for sponsorship in self.search(search_domain):
            reminder_search = [
                ("config_id", "in", reminder_conf_list.ids),
                ("state", "=", "done"),
                ("object_ids", "like", str(sponsorship.id)),
            ]
            # Look if first reminder was sent previous month (send second
            # reminder in that case)
            # avoid taking into account reminder that the partner already took care of
            # we substract month due to the first of the month to get the older threshold
            # this also prevent reminder_1 to be sent after an already sent reminder_2
            older_threshold = first_day_of_month - relativedelta(
                months=sponsorship.months_due
            )

            has_first_reminder = partnerCommunicationJob.search_count(
                reminder_search
                + [
                    ("sent_date", ">=", older_threshold),
                    ("sent_date", "<", twenty_days_ago),
                ]
            )
            if has_first_reminder:
                has_second_reminder = partnerCommunicationJob.search_count(
                    reminder_search
                    + [
                        ("sent_date", ">=", older_threshold),
                        ("sent_date", "<", twenty_days_ago),
                        ("config_id", "=", reminder_conf_list[1].id),
                    ]
                )
                if has_second_reminder:
                    contracts_eligible_reminder_dict["third"] += sponsorship
                contracts_eligible_reminder_dict["second"] += sponsorship
            else:
                # Create first reminder only if one was not already created less
                # than twenty days ago
                has_first_reminder = partnerCommunicationJob.search_count(
                    reminder_search + [("sent_date", ">=", twenty_days_ago)]
                )
                if not has_first_reminder:
                    contracts_eligible_reminder_dict["first"] += sponsorship
        contracts_eligible_reminder_dict["first"].with_delay().send_communication(
            reminder_conf_list[0], correspondent=False
        )
        contracts_eligible_reminder_dict["second"].with_delay().send_communication(
            reminder_conf_list[1], correspondent=False
        )
        contracts_eligible_reminder_dict["third"].with_delay().send_communication(
            reminder_conf_list[2], correspondent=False
        )
        _logger.info("Sponsorship Reminders created!")
        return True
