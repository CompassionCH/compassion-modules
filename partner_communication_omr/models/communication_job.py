##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from io import BytesIO

from reportlab.lib.colors import white
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from odoo import api, models

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
    from PyPDF2.utils import PdfReadError
except ImportError:
    _logger.warning(
        "Please install PyPDF2 for generating OMR codes in "
        "Printed partner communications"
    )


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.extend(
            [
                "omr_enable_marks",
                "omr_should_close_envelope",
                "omr_add_attachment_tray_1",
                "omr_add_attachment_tray_2",
                "omr_top_mark_x",
                "omr_top_mark_y",
                "omr_single_sided",
            ]
        )
        return super()._get_default_vals(vals, default_vals)

    def add_omr_marks(self, pdf_data, is_latest_document):
        # Documentation
        # http://meteorite.unm.edu/site_media/pdf/reportlab-userguide.pdf
        # https://pythonhosted.org/PyPDF2/PdfFileReader.html
        # https://stackoverflow.com/a/17538003
        # https://gist.github.com/kzim44/5023021
        # https://www.blog.pythonlibrary.org/2013/07/16/pypdf-how-to-write-a-pdf-to-memory/
        self.ensure_one()

        pdf_buffer = BytesIO()
        pdf_buffer.write(pdf_data)

        try:
            existing_pdf = PdfFileReader(pdf_buffer)
        except PdfReadError:
            # Cannot add OMR marks to non-pdf attachments.
            # The folding machine will unfortunately block here.
            return pdf_data

        output = PdfFileWriter()
        total_pages = existing_pdf.getNumPages()

        def lastpair(a):
            b = a - 1
            if self.omr_single_sided or b % 2 == 0:
                return b
            return lastpair(b)

        # print latest omr mark on latest pair page (recto)
        latest_omr_page = lastpair(total_pages)

        for page_number in range(total_pages):
            page = existing_pdf.getPage(page_number)
            # only print omr marks on pair pages (recto)
            if self.omr_single_sided or page_number % 2 == 0:
                is_latest_page = is_latest_document and page_number == latest_omr_page
                marks = self._compute_marks(is_latest_page)
                omr_layer = self._build_omr_layer(marks)
                page.mergePage(omr_layer)
            output.addPage(page)

        out_buffer = BytesIO()
        output.write(out_buffer)

        return out_buffer.getvalue()

    def _compute_marks(self, is_latest_page):
        marks = [
            True,  # Start mark (compulsory)
            is_latest_page,
            is_latest_page and self.omr_add_attachment_tray_1,
            is_latest_page and self.omr_add_attachment_tray_2,
            is_latest_page and not self.omr_should_close_envelope,
        ]
        parity_check = sum(marks) % 2 == 0
        marks.append(parity_check)
        marks.append(True)  # End mark (compulsory)
        return marks

    def _build_omr_layer(self, marks):
        self.ensure_one()
        padding_x = 4.2 * mm
        padding_y = 8.5 * mm
        top_mark_x = self.omr_top_mark_x * mm
        top_mark_y = self.omr_top_mark_y * mm
        mark_y_spacing = 4 * mm

        mark_width = 6.5 * mm
        marks_height = (len(marks) - 1) * mark_y_spacing

        _logger.debug(
            "Mailer DS-75i OMR Settings: 1=%s 2=%s",
            str((297 * mm - top_mark_y) / mm),
            str((top_mark_x + mark_width / 2) / mm + 0.5),
        )

        omr_buffer = BytesIO()
        omr_canvas = Canvas(omr_buffer)
        omr_canvas.setLineWidth(0.2 * mm)

        # add a white background for the omr code
        omr_canvas.setFillColor(white)
        omr_canvas.rect(
            x=top_mark_x - padding_x,
            y=top_mark_y - marks_height - padding_y,
            width=mark_width + 2 * padding_x,
            height=marks_height + 2 * padding_y,
            fill=True,
            stroke=False,
        )

        for offset, mark in enumerate(marks):
            mark_y = top_mark_y - offset * mark_y_spacing
            if mark:
                omr_canvas.line(top_mark_x, mark_y, top_mark_x + mark_width, mark_y)

        # Close the PDF object cleanly.
        omr_canvas.showPage()
        omr_canvas.save()

        # move to the beginning of the BytesIO buffer
        omr_buffer.seek(0)
        omr_pdf = PdfFileReader(omr_buffer)

        return omr_pdf.getPage(0)
