import base64
import logging

from odoo import fields, models
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class DownloadPrintJobWizard(models.TransientModel):
    _name = "partner.communication.download.print.job.wizard"
    _description = "Partner Communication - Download Print Job Wizard"

    communication_job_ids = fields.Many2many(
        "partner.communication.job",
        "partner_communication_download_print_rel",
        string="Letters",
        required=True,
        readonly=True,
    )
    attachment_ids = fields.One2many(
        "partner.communication.attachment",
        string="Attachments",
        compute="_compute_attachment_ids",
    )
    merged_name = fields.Char(compute="_compute_merge_names")
    letters_name = fields.Char(compute="_compute_merge_names")
    attachments_name = fields.Char(compute="_compute_merge_names")
    merged_data = fields.Binary("All Merged", compute="_compute_merged_data")
    letters_data = fields.Binary("Letters Only", compute="_compute_merged_data")
    attachments_data = fields.Binary("Attachments Only", compute="_compute_merged_data")

    def _compute_attachment_ids(self):
        for wiz in self:
            wiz.attachment_ids = wiz.communication_job_ids.mapped("attachment_ids")

    def _compute_merged_data(self):
        for wiz in self:
            all_merged, letters_merged, attachments_merged = [], [], []
            for job in wiz.communication_job_ids:
                if job.printed_pdf_data:
                    job_data = base64.b64decode(job.printed_pdf_data)
                    all_merged.append(job_data)
                    letters_merged.append(job_data)

                pdf_attachments = job.attachment_ids.filtered(
                    lambda a: a.printed_pdf_data
                    and a.attachment_id.mimetype == "application/pdf"
                )
                attachments_data = [
                    base64.b64decode(a.printed_pdf_data) for a in pdf_attachments
                ]
                all_merged.extend(attachments_data)
                attachments_merged.extend(attachments_data)
            wiz.merged_data = (
                base64.b64encode(merge_pdf(all_merged)) if all_merged else False
            )
            wiz.letters_data = (
                base64.b64encode(merge_pdf(letters_merged)) if letters_merged else False
            )
            wiz.attachments_data = (
                base64.b64encode(merge_pdf(attachments_merged))
                if attachments_merged
                else False
            )

    def _compute_merge_names(self):
        for wiz in self:
            sent_date = fields.Date.to_string(wiz.communication_job_ids[0].sent_date)
            config_name = wiz.communication_job_ids.config_id[0].name
            wiz.merged_name = f"{sent_date}_{config_name}.pdf"
            wiz.letters_name = (
                f"{sent_date}_{config_name}_Letters.pdf" if wiz.letters_data else False
            )
            wiz.attachments_name = (
                f"{sent_date}_{config_name}_Attachments.pdf"
                if wiz.attachments_data
                else False
            )

    def clear_data(self):
        self.mapped("communication_job_ids.attachment_ids").write(
            {"printed_pdf_data": False}
        )
        self.mapped("communication_job_ids").write({"printed_pdf_data": False})
        return True
