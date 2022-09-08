##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)

try:
    from wand.image import Image
except ImportError:
    _logger.warning("Please install wand to use PDF Previews")


class PdfPreviewWizard(models.TransientModel):
    """
    Generate pdf of communication.
    """

    _name = "partner.communication.pdf.wizard"
    _description = "Partner Communication - PDF Wizard"

    communication_id = fields.Many2one(
        "partner.communication.job", required=True, ondelete="cascade", readonly=False
    )
    preview = fields.Image(compute="_compute_pdf")
    state = fields.Selection(related="communication_id.send_mode")
    send_state = fields.Selection(related="communication_id.state")
    body_html = fields.Html(compute="_compute_html")

    def _compute_pdf(self):
        if self.state != "physical":
            self.preview = False
            return
        comm = self.communication_id
        report = comm.report_id.with_context(
            lang=comm.partner_id.lang, must_skip_send_to_printer=True, bin_size=False
        )
        data = report._render_qweb_pdf(comm.ids)
        with Image(blob=data[0], resolution=150) as pdf_image:
            preview = base64.b64encode(pdf_image.make_blob(format="jpeg"))

        self.preview = preview

    def _compute_html(self):
        comm = self.communication_id
        template = getattr(comm.email_template_id, "sendgrid_localized_template", False)
        if template:
            body_html = template.html_content.replace("<%body%>", comm.body_html)
            self.body_html = body_html

        self.body_html = comm.body_html

    def send(self):
        return self.communication_id.send()
