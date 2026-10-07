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
        stream_res_ids = {}
        failed_scan_res_ids = set()
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
                failed_scan_res_ids.add(attachment.res_id)
                continue
            if stream is None:
                _logger.warning(
                    "Skipping correspondence letter scan (attachment %s) "
                    "with unrecognized mimetype %s",
                    attachment.id,
                    attachment.mimetype,
                )
                failed_scan_res_ids.add(attachment.res_id)
                continue
            streams.append(stream)
            stream_res_ids[id(stream)] = attachment.res_id

        # A letter whose scan attachment exists but failed to convert is
        # treated the same as one with no scan at all: render it from the
        # QWeb template instead of just dropping it, so a batch where every
        # scan fails still produces the letters, not a silent empty PDF.
        without_scan_ids = (
            set(res_ids) - {att.res_id for att in attachments}
        ) | failed_scan_res_ids
        if without_scan_ids:
            pdf_bytes, _ = super()._render_qweb_pdf(
                report_ref, res_ids=list(without_scan_ids), data=data
            )
            streams.append(BytesIO(pdf_bytes))

        # A scan whose mimetype is application/pdf can still hold malformed
        # content - to_pdf_stream() doesn't validate that, so such a stream
        # reaches here and only fails once _merge_pdfs() actually tries to
        # parse it. Map it back to its correspondence so it can still be
        # rendered from QWeb instead of just vanishing from the batch.
        merge_rejected_res_ids = set()

        def _skip_corrupted_letter(error, error_stream):
            res_id = stream_res_ids.get(id(error_stream))
            _logger.warning(
                "Skipping a corrupted correspondence letter scan "
                "(correspondence %s) while merging PDFs: %s",
                res_id,
                error,
            )
            if res_id is not None:
                merge_rejected_res_ids.add(res_id)

        with self._merge_pdfs(
            streams, handle_error=_skip_corrupted_letter
        ) as pdf_merged_stream:
            if not merge_rejected_res_ids:
                return pdf_merged_stream.getvalue(), "pdf"
            pdf_merged_stream.seek(0)
            fallback_bytes, _ = super()._render_qweb_pdf(
                report_ref, res_ids=list(merge_rejected_res_ids), data=data
            )
            with self._merge_pdfs(
                [pdf_merged_stream, BytesIO(fallback_bytes)]
            ) as final_stream:
                return final_stream.getvalue(), "pdf"
