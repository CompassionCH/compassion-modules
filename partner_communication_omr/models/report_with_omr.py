import logging
from io import BytesIO

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
except ImportError:
    _logger.warning("Please install library PyPDF2")


class OmrAwareReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, res_ids=None, data=None):
        communication_job_model = "partner.communication.job"
        if self.model == communication_job_model:
            jobs = self.env[communication_job_model].browse(res_ids)
            if jobs.filtered("omr_enable_marks"):
                # Add OMR marks on pages of the jobs :
                # We must reconstruct the PDF job by job.
                output = PdfFileWriter()
                for job in jobs:
                    document, document_type = super()._render_qweb_pdf(
                        job.ids, data=data)
                    if job.omr_enable_marks:
                        is_latest_document = not job.attachment_ids.filtered(
                            "attachment_id.enable_omr"
                        )
                        document = job.add_omr_marks(document, is_latest_document)
                    pdf_buffer = BytesIO()
                    pdf_buffer.write(document)
                    job_pdf = PdfFileReader(pdf_buffer)
                    for i in range(0, job_pdf.getNumPages()):
                        output.addPage(job_pdf.getPage(i))
                out_buffer = BytesIO()
                output.write(out_buffer)
                res = out_buffer.getvalue()
                return res, document_type

        return super()._render_qweb_pdf(res_ids, data=data)
