# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, models, _
from odoo.tools import append_content_to_html
from odoo.addons.sponsorship_compassion.models.product_names import GIFT_REF

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
        - Append the quote of previous e-mail to the body of the message.
        - Add gift payment slips for "Gift/Payment slip" and "Christmas Gift Fund"
        """
        result = super().onchange_template_id(
            template_id, composition_mode, model, res_id
        )

        # Add reply quote
        reply_quote = self.env.context.get("reply_quote")
        if reply_quote:
            result["value"]["body"] = append_content_to_html(
                result["value"]["body"], "<br/><br/>" + reply_quote, plaintext=False
            )

        # Clear previous attachments
        self.attachment_ids = None

        # Add gift payment slips
        template = self.env["mail.template"].browse(template_id)
        template_name = template.with_context(lang="en_US").name
        partner = self.partner_ids[0]
        sponsorships = partner.sponsorship_ids

        if template_name == "Gift/Payment slip" and sponsorships:
            refs = [GIFT_REF[0], GIFT_REF[1], GIFT_REF[2]]
            report = self.env.ref("report_compassion.report_3bvr_gift_sponsorship")
            payment_slips = self.get_payment_slips(refs, report, sponsorships.ids)
            result["value"]["attachment_ids"] = payment_slips.ids

        if template_name == "Christmas Gift Fund":
            refs = ["gen_christmas"]
            report = self.env.ref("report_compassion.report_bvr_fund")
            payment_slips = self.get_payment_slips(refs, report, partner.id)
            result["value"]["attachment_ids"] = payment_slips.ids

        return result

    def get_payment_slips(self, refs, report, doc_ids):
        """
        Returns the pdf of selected gift payment slips
        :return: "ir.attachment" instance
        """
        product = self.env["product.product"].search([("default_code", "in", refs)])
        data = {
            "product_ids": product.ids,
            "product_id": product.ids,
            "background": True,
        }
        pdf, _ = report.with_context(must_skip_send_to_printer=True).render_qweb_pdf(
            doc_ids, data=data
        )
        file_name = _("gift payment slips") + ".pdf"

        return self.env['ir.attachment'].create({
            'name': file_name,
            'datas_fname': file_name,
            'datas': base64.encodebytes(pdf),
        })
