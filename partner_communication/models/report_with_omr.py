# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
    def get_pdf(self, docids, report_name, html=None, data=None):
        report = self._get_report_from_name(report_name)
        communication_job_model = 'partner.communication.job'
        if report.model == communication_job_model:
            jobs = self.env[communication_job_model].browse(docids)
            if jobs.filtered('omr_enable_marks'):
                # Add OMR marks on pages of the jobs :
                # We must reconstruct the PDF job by job.
                output = PdfFileWriter()
                for job in jobs:
                    job_data = super(OmrAwareReport, self) \
                        .get_pdf(job.ids, report_name, html=html, data=data)
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

        return super(OmrAwareReport, self).get_pdf(docids, report_name,
                                                   html=html, data=data)
