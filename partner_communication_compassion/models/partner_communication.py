##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from io import BytesIO

from PyPDF2 import PdfFileReader, PdfFileWriter

from odoo import _, fields, models
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)


class PartnerCommunication(models.Model):
    _inherit = "partner.communication.job"

    utm_campaign_id = fields.Many2one("utm.campaign", readonly=False)

    def get_correspondence_attachments(self, letters=None):
        """
        Include PDF of letters if the send_mode is to print the letters.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        # Report is used for print configuration
        report = "partner_communication.a4_communication"
        if letters is None:
            letters = self.get_objects()
        if self.send_mode == "physical":
            for letter in letters:
                try:
                    attachments[letter.file_name] = [
                        report,
                        self._convert_pdf(letter.letter_image),
                    ]
                except MissingError:
                    _logger.warning("Missing letter image", exc_info=True)
                    self.send_mode = False
                    self.auto_send = False
                    self.message_post(
                        body=_("The letter image is missing!"),
                        subject=_("Missing letter"),
                    )
                    continue
        else:
            # Attach directly a zip in the letters
            letters.attach_zip()
        return attachments

    def final_letter_attachment(self):
        """Include PDF of final letter if any exists. Remove any other correspondence
        that would send it and link the letter to the current communication."""
        self.ensure_one()
        sponsorships = self.get_objects()
        attachments = dict()
        final_type = self.env.ref("sbc_compassion.correspondence_type_final")
        final_letters = self.env["correspondence"].search(
            [
                ("sponsorship_id", "in", sponsorships.ids),
                ("communication_type_ids", "=", final_type.id),
                ("sent_date", "=", False),
                ("email_read", "=", False),
            ]
        )
        if final_letters:
            final_letters.mapped("communication_id").cancel()
            final_letters.write({"communication_id": self.id})
            attachments = self.get_correspondence_attachments(final_letters)
        return attachments

    def get_child_picture_attachment(self):
        """
        Attach child pictures to communication. It directly attach them
        to the communication if sent by e-mail and therefore does
        return an empty dictionary.
        :return: dict {}
        """
        self.ensure_one()
        res = dict()
        biennial = self.env.ref("partner_communication_compassion.biennial")
        if self.config_id == biennial:
            if self.send_mode == "physical":
                # In this case the photo is printed from Smartphoto and manually added
                return res
            children = self.get_objects()
        else:
            children = self.get_objects().mapped("child_id")
        pdf = self._get_pdf_from_data(
            {"doc_ids": children.ids},
            self.env.ref("partner_communication_compassion.report_child_picture"),
        )
        name = children.get_list("local_id", 1, _("pictures")) + ".pdf"
        res[name] = ("partner_communication_compassion.child_picture", pdf)
        return res

    def _convert_pdf(self, pdf_data):
        """
        Converts all pages of PDF in A4 format if communication is
        printed.
        :param pdf_data: binary data of original pdf
        :return: binary data of converted pdf
        """
        if self.send_mode != "physical":
            return pdf_data

        pdf = PdfFileReader(BytesIO(base64.b64decode(pdf_data)))
        convert = PdfFileWriter()
        a4_width = 594.48
        a4_height = 844.32  # A4 units in PyPDF
        for i in range(0, pdf.numPages):
            # translation coordinates
            tx = 0
            ty = 0
            page = pdf.getPage(i)
            corner = [float(x) for x in page.mediaBox.getUpperRight()]
            if corner[0] > a4_width or corner[1] > a4_height:
                page.scaleBy(max(a4_width / corner[0], a4_height / corner[1]))
            elif corner[0] < a4_width or corner[1] < a4_height:
                tx = (a4_width - corner[0]) / 2
                ty = (a4_height - corner[1]) / 2
            convert.addBlankPage(a4_width, a4_height)
            convert.getPage(i).mergeTranslatedPage(page, tx, ty)
        output_stream = BytesIO()
        convert.write(output_stream)
        output_stream.seek(0)
        return base64.b64encode(output_stream.read())

    def _get_pdf_from_data(self, data, report_ref):
        """
        Helper to get the PDF base64 encoded given report ref and its data.
        :param data: values for the report generation
        :param report_ref: report xml id
        :return: base64 encoded PDF
        """
        report_str = report_ref._render_qweb_pdf(data["doc_ids"], data)
        if isinstance(report_str, (list, tuple)):
            report_str = report_str[0]
        elif isinstance(report_str, bool):
            report_str = ""

        output = None
        if isinstance(report_str, bytes):
            output = base64.encodebytes(report_str)
        else:
            base64.encodebytes(report_str.encode())
        return output

    def send(self):
        res = super().send()
        biennial = self.env.ref("partner_communication_compassion.biennial")
        biennials = self.filtered(
            lambda j: j.state == "done" and j.config_id == biennial
        )
        if biennials:
            for child in biennials.get_objects():
                child.sponsorship_ids[0].new_picture = False
        return res

    def cancel(self):
        res = super().cancel()
        biennial = self.env.ref("partner_communication_compassion.biennial")
        biennials = self.filtered(lambda j: j.config_id == biennial)
        if biennials:
            for child in biennials.get_objects():
                child.sponsorship_ids[0].new_picture = False
        return res
