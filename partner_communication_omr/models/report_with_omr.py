import logging
from io import BytesIO

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    _logger.warning("Please install library pypdf")


class OmrAwareReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        communication_job_model = "partner.communication.job"

        # Check if we are rendering the report for the communication job
        if self.model == communication_job_model:
            jobs = self.env[communication_job_model].browse(res_ids)

            if jobs.filtered("omr_enable_marks"):
                # Add OMR marks on pages of the jobs :
                # We must reconstruct the PDF job by job.
                output = PdfWriter()

                for job in jobs:
                    # Pass report_ref to the super method
                    document, document_type = super()._render_qweb_pdf(
                        report_ref, job.ids, data=data
                    )

                    if job.omr_enable_marks:
                        is_latest_document = not job.attachment_ids.filtered(
                            "attachment_id.enable_omr"
                        )
                        document = job.add_omr_marks(document, is_latest_document)

                    pdf_buffer = BytesIO()
                    pdf_buffer.write(document)
                    job_pdf = PdfReader(pdf_buffer)

                    # pypdf syntax: iterate over pages directly
                    for page in job_pdf.pages:
                        output.add_page(page)

                out_buffer = BytesIO()
                output.write(out_buffer)
                res = out_buffer.getvalue()
                return res, document_type

        # Pass report_ref to the super method
        return super()._render_qweb_pdf(report_ref, res_ids, data=data)
