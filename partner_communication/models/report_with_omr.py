from io import StringIO
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    from pyPdf import PdfFileWriter, PdfFileReader
except ImportError:
    _logger.warning("Please install library pyPdf")


class OmrAwareReport(models.Model):

    _inherit = 'ir.actions.report'

    @api.model
    def render_qweb_pdf(self, docids, data=None):
        communication_job_model = 'partner.communication.job'
        if self.model == communication_job_model:
            jobs = self.env[communication_job_model].browse(docids)
            if jobs.filtered('omr_enable_marks'):
                # Add OMR marks on pages of the jobs :
                # We must reconstruct the PDF job by job.
                output = PdfFileWriter()
                for job in jobs:
                    job_data = super().render_qweb_pdf(job.ids, data=data)
                    if job.omr_enable_marks:
                        is_latest_document = not job.attachment_ids.filtered(
                            'attachment_id.enable_omr'
                        )
                        job_data = job.add_omr_marks(job_data,
                                                     is_latest_document)
                    pdf_buffer = StringIO()
                    pdf_buffer.write(job_data)
                    job_pdf = PdfFileReader(pdf_buffer)
                    for i in range(0, job_pdf.getNumPages()):
                        output.addPage(job_pdf.getPage(i))
                out_buffer = StringIO()
                output.write(out_buffer)
                res = out_buffer.getvalue()
                return res

        return super().get_pdf(docids, data=data)
