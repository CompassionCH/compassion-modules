from odoo import models


class CompassionHold(models.Model):
    _inherit = "compassion.hold"

    def postpone_no_money_hold(self, additional_text=None):
        """
        Send a communication to sponsor for reminding the payment.
        :param additional_text: text to add in the notification to hold owner
        :return: None
        """
        notification_text = (
            "\n\nA reminder has been prepared for the " "sponsor {} ({})"
        )
        failed = self.env[self._name]
        for i in range(1, 3):
            reminder_conf = self.env.ref(f"partner_communication_reminder.sponsorship_activation_reminder_{i}")
            reminders = self.env["partner.communication.job"].search([
                ("config_id", "=", reminder_conf.id),
                ("state", "=", "pending")
            ])
            if reminders:
                pending_holds = reminders.get_objects().mapped(
                    "child_id.hold_id")
                (pending_holds & self).write({"no_money_extension": i - 1})

                for hold in self.with_context(
                        default_auto_send=False,
                        default_print_subject=False,
                        default_print_header=True,
                ):
                    sponsorship = hold.child_id.sponsorship_ids[:1]
                    sponsor = hold.child_id.sponsor_id
                    # Filter draft sponsorships and where we wait for
                    # the bank authorization
                    if sponsorship.state == "draft" or (
                            sponsorship.state == "mandate" and sponsor.bank_ids
                    ):
                        try:
                            previous_extension = hold.no_money_extension
                            super(CompassionHold, hold).postpone_no_money_hold()
                            if previous_extension < hold.no_money_extension:
                                hold.no_money_extension = previous_extension
                            continue
                        except:
                            failed += hold
                            continue
                    # Cancel old invoices
                    try:
                        if len(sponsorship.due_invoice_ids) > 1:
                            sponsorship.due_invoice_ids[:-1].action_invoice_cancel()
                        super(CompassionHold, hold).postpone_no_money_hold(
                            notification_text.format(sponsor.name, sponsor.ref)
                        )
                        sponsorship.send_communication(reminder_conf, correspondent=False)
                    except:
                        failed += hold
        if failed:
            # Send warning to Admin users
            child_codes = failed.mapped("child_id").read(["local_id"])
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            links = [
                f'<a href="{base_url}/web#id={data["id"]}&'
                f"view_type=form&model=compassion.child"
                f'&menu_id=442&action=581">{data["local_id"]}</a>'
                for data in child_codes
            ]
            hold_string = list()
            for i in range(0, len(failed)):
                hold_string.append(failed[i].hold_id + " (" + links[i] + " )")
            self.env["mail.mail"].create(
                {
                    "subject": "URGENT: Postpone no money holds failed!",
                    "author_id": self.env.user.partner_id.id,
                    "recipient_ids": [(6, 0, [18000, 13])],
                    "body_html": "These holds should be urgently verified: <br/>"
                                 "<br/>" + ", ".join(hold_string),
                }
            ).send()

        super().postpone_no_money_hold(additional_text)
