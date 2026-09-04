import logging
from io import BytesIO

from odoo import models
from odoo.tools.pdf import to_pdf_stream

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # For correspondence reports, if a letter has a pre-scanned PDF, use that PDF
        # directly instead of rendering the QWeb template.
        # Merge it with other rendered letters.
        # report_ref can be an id, a record, an xmlid or a report_name (see
        # _get_report()'s docstring) - normalize before comparing.
        report = self._get_report(report_ref)
        if (
            report.report_name != "sbc_compassion.correspondence_report_qweb"
            or not res_ids
        ):
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "correspondence"),
                ("res_id", "in", res_ids),
                ("res_field", "=", "sponsor_letter_scan"),
            ]
        )
        if not attachments:
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        streams = []
        for attachment in attachments:
            try:
                stream = to_pdf_stream(attachment)
            except Exception:
                _logger.warning(
                    "Skipping unreadable correspondence letter scan "
                    "(attachment %s) while generating the PDF",
                    attachment.id,
                    exc_info=True,
                )
                continue
            if stream is None:
                _logger.warning(
                    "Skipping correspondence letter scan (attachment %s) "
                    "with unrecognized mimetype %s",
                    attachment.id,
                    attachment.mimetype,
                )
                continue
            streams.append(stream)

        without_scan_ids = set(res_ids) - {att.res_id for att in attachments}
        if without_scan_ids:
            pdf_bytes, _ = super()._render_qweb_pdf(
                report_ref, res_ids=list(without_scan_ids), data=data
            )
            streams.append(BytesIO(pdf_bytes))

        def _skip_corrupted_letter(error, error_stream):
            _logger.warning(
                "Skipping a corrupted correspondence letter scan while "
                "merging PDFs: %s",
                error,
            )

        with self._merge_pdfs(
            streams, handle_error=_skip_corrupted_letter
        ) as pdf_merged_stream:
            return pdf_merged_stream.getvalue(), "pdf"
