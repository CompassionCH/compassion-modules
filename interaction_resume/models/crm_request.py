from datetime import timedelta

from odoo import api, models
from odoo.tools.mail import html2plaintext


class CrmRequest(models.Model):
    _inherit = ["crm.claim", "interaction.source"]
    _name = "crm.claim"

    def _get_interaction_data(self, partner_id):
        res = []
        partner = self.env["res.partner"].browse(partner_id)
        partners = (
            (
                self.env["res.partner"]
                .with_context(active_test=False)
                .search([("email", "=", partner.email)])
            )
            | partner
            | partner.other_contact_ids
        )
        for claim in self:
            # All thread discussion messages
            messages = (
                claim.message_ids.filtered(
                    lambda m: (m.partner_ids & partners) or m.author_id in partners
                )
                .filtered("subject")
                .sorted("date")
            )
            first_message = messages[:1]
            if not (
                first_message
                and abs(first_message.date - claim.date) < timedelta(minutes=1)
            ):
                # Contactus form if applicable
                res.append(
                    {
                        "partner_id": partner_id,
                        "res_model": self._name,
                        "res_id": claim.id,
                        "direction": "in",
                        "date": claim.date or claim.create_date,
                        "email": claim.email_from or claim.partner_id.email,
                        "communication_type": "Support",
                        "subject": "CRM Request: " + str(claim.name),
                        "body": html2plaintext(claim.description).replace("\n\n", "\n"),
                        "has_attachment": False,
                        "tracking_status": False,
                    }
                )
            res.extend(
                [
                    {
                        "partner_id": partner_id,
                        "res_model": self._name,
                        "res_id": claim.id,
                        "direction": "in" if message.author_id in partners else "out",
                        "date": message.date,
                        "email": claim.email_from or claim.partner_id.email,
                        "communication_type": "Support",
                        "subject": message.subject,
                        "body": html2plaintext(message.body).replace("\n\n", "\n"),
                        "has_attachment": bool(message.attachment_ids),
                        "tracking_status": message.mail_tracking_ids[:1].state,
                    }
                    for message in messages
                ]
            )
        return res

    def _get_interaction_partner_domain(self, partner):
        if not partner.email:
            return [
                "|",
                ("partner_id", "=", partner.id),
                ("partner_id", "in", partner.other_contact_ids.ids),
            ]
        return [
            "|",
            "|",
            "|",
            ("partner_id", "=", partner.id),
            ("partner_id.email", "=", partner.email),
            ("partner_id", "in", partner.other_contact_ids.ids),
            ("email_from", "=", partner.email),
        ]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger timeline update for anonymous users by email
        """
        claims = super().create(vals_list)
        for claim in claims:
            partner_to_update = claim.partner_id
            # If no partner_id, try to find a partner using email
            if not partner_to_update and claim.email_from:
                partner_to_update = self.env["res.partner"].search(
                    [("email", "=", claim.email_from)], limit=1
                )

            if partner_to_update:
                partner_to_update.with_delay(
                    channel="root.partner_communication",
                    priority=100,
                    identity_key=partner_to_update._name
                    + ".fetch_interactions."
                    + str(partner_to_update.id),
                ).fetch_interactions()
        return claims

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)

        partner_to_update = self.partner_id
        # If no partner_id, try to find a partner using email
        if not partner_to_update:
            partner_to_update = self.env["res.partner"].search(
                [("email", "=", self.email_from)], limit=1, order="customer_rank desc"
            )

        if partner_to_update:
            self.partner_id.with_delay(
                channel="root.partner_communication",
                priority=100,
                identity_key=self.partner_id._name
                + ".fetch_interactions."
                + str(self.partner_id.id),
            ).fetch_interactions()
        return res
