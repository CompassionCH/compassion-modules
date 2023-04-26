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

from odoo import models, _

_logger = logging.getLogger(__name__)

class PartnerCommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    def get_reminder_bvr(self):
        """
        Attach sponsorship due payment slip with background for sending by
        e-mail.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()

        payment_mode = sponsorships.with_context(lang="en_US").mapped(
            "payment_mode_id.name"
        )[0]
        # LSV-DD Waiting reminders special case
        if "Waiting Reminder" in self.config_id.name and (
                "LSV" in payment_mode or "Postfinance" in payment_mode
        ):
            if not self.partner_id.bank_ids or not self.partner_id.valid_mandate_id:
                # Don't put payment slip if we just wait the authorization form
                pm = self.env['account.payment.mode'].search([
                    ('name', '=', payment_mode)])
                return {"lsv_form.pdf": ["partner_communication.a4_no_margin",
                                         pm.payment_method_id.lsv_form_pdf]}

        # Put product sponsorship to print the payment slip for physical print.
        if self.send_mode and "physical" in self.send_mode:
            self.product_id = self.env["product.product"].search(
                [("default_code", "=", "sponsorship")], limit=1
            )
            return dict()

        # In other cases, attach the payment slip.
        report_name = "report_compassion.bvr_due"
        data = {"background": True, "doc_ids": sponsorships.ids, "disable_scissors": True}
        pdf = self._get_pdf_from_data(
            data, self.env.ref("report_compassion.report_bvr_due")
        )
        return {_("sponsorship due.pdf"): [report_name, pdf]}
