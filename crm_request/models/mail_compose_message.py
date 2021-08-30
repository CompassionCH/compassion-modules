# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import append_content_to_html


class MailComposer(models.TransientModel):
    """
    Extend the mail composer so that it can send message to archived partner,
    and put back the selected partner in the claim in case it was not linked.
    """

    _inherit = "mail.compose.message"

    @api.multi
    def send_mail(self, auto_commit=False):

        res = super().send_mail(auto_commit)

        # Put back selected partner into claim
        if self.env.context.get("claim_no_partner"):
            gen_mail = self.env["mail.mail"].search(
                [("res_id", "=", self.res_id), ("model", "=", "crm.claim")], limit=1
            )
            self.env["crm.claim"].browse(self.res_id).write(
                {"partner_id": gen_mail.recipient_ids[:1].id}
            )

        # Assign current user to request
        if self.model == "crm.claim":
            self.env["crm.claim"].browse(self.res_id).write(
                {"user_id": self.env.uid}
            )

        return res

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """
        Append the quote of previous e-mail to the body of the message.
        """
        result = super(MailComposer, self.with_context(
            lang=self.env.context.get('salutation_language', self.env.lang))
        ).onchange_template_id(
            template_id, composition_mode, model, res_id
        )
        reply_quote = self.env.context.get("reply_quote")
        if reply_quote:
            result["value"]["body"] = append_content_to_html(
                result["value"]["body"], "<br/><br/>" + reply_quote, plaintext=False
            )
        return result
