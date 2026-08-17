from io import BytesIO

from odoo import models
from odoo.tools.pdf import to_pdf_stream


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

        streams = [to_pdf_stream(attachment) for attachment in attachments]
        without_scan_ids = set(res_ids) - {att.res_id for att in attachments}
        if without_scan_ids:
            pdf_bytes, _ = super()._render_qweb_pdf(
                report_ref, res_ids=list(without_scan_ids), data=data
            )
            streams.append(BytesIO(pdf_bytes))

        with self._merge_pdfs(streams) as pdf_merged_stream:
            return pdf_merged_stream.getvalue(), "pdf"
