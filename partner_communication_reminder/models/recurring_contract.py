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
        reminder_confs = self.env["partner.communication.config"]
        for i in range(1, 4):
            reminder_confs += self.env.ref(
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
        eligible_reminders = {
            "first": self.env[(self._name)],
            "second": self.env[(self._name)],
            "third": self.env[(self._name)],
        }
        for sponsorship in self.search(search_domain):
            reminder_search = [
                ("config_id", "in", reminder_confs.ids),
                ("state", "=", "done"),
                ("object_ids", "like", str(sponsorship.id)),
            ]


            # To avoid taking into account reminder that the partner already took care of
            # we subtract month due to the first of the month to get the older threshold
            # this also prevent reminder_1 to be sent after an already sent reminder_2
            older_threshold = first_day_of_month - relativedelta(
                months=sponsorship.months_due
            )

            # Search for every reminder more recent than older_threshold
            reminders = partnerCommunicationJob.search(
                reminder_search + [("sent_date", ">=", older_threshold)]
            )

            # Group reminders by configuration ID
            reminders_by_config = {conf.id: [] for conf in reminder_confs}
            for reminder in reminders:
                reminders_by_config.get(reminder.config_id.id, []).append(reminder)

            first_reminders = reminders_by_config[reminder_confs[0].id]
            second_reminders = reminders_by_config[reminder_confs[1].id]

            # Look if first reminder was sent previous month
            old_first = any(r.sent_date < twenty_days_ago for r in first_reminders)
            if old_first:
                old_second = any(r.sent_date < twenty_days_ago for r in second_reminders)
                recent_second = any(r.sent_date >= twenty_days_ago for r in second_reminders)

                if old_second:
                    # The 2nd reminder has been sent at least 20 days ago, then
                    # we can send the 3rd.
                    eligible_reminders["third"] += sponsorship
                elif not recent_second:
                    eligible_reminders["second"] += sponsorship
                # If recent 2nd reminder, do nothing

            else:
                if not first_reminders or all(r.sent_date < twenty_days_ago for r in first_reminders):
                    eligible_reminders["first"] += sponsorship
                # If recent 1st reminder, do nothing

        for key, config in zip(["first", "second", "third"], reminder_confs):
            sponsorships = eligible_reminders[key]
            if sponsorships:
                sponsorships.with_delay(
                    channel="root.partner_communication",
                    priority=500,
                    identity_key=f"create_reminder_communication.{sponsorships.ids}",
                ).send_communication(config, correspondent=False)
        _logger.info("Sponsorship Reminders created!")
        return True
