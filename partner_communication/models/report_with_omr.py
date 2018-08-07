# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class OmrAwareReport(models.Model):

    _inherit = 'report'

    @api.model
    def get_pdf(self, docids, report_name, html=None, data=None):
        pdf_data = super(OmrAwareReport, self) \
            .get_pdf(docids, report_name, html=html, data=data)
        report = self._get_report_from_name(report_name)
        communication_job_model = 'partner.communication.job'
        if report.model == communication_job_model:
            job = self.env[communication_job_model].browse(docids).exists()
            if job.omr_enable_marks:
                is_latest_document = not job.attachment_ids.filtered(
                    'attachment_id.enable_omr'
                )
                return job.add_omr_marks(
                    pdf_data, is_latest_document
                )
        return pdf_data
