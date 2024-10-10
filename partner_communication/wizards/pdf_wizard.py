##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PdfPreviewWizard(models.TransientModel):
    """
    Generate pdf of communication.
    """

    _name = "partner.communication.pdf.wizard"
    _description = "Partner Communication - PDF Wizard"

    communication_id = fields.Many2one(
        "partner.communication.job", required=True, ondelete="cascade", readonly=False
    )
    preview = fields.Html(compute="_compute_preview")
    state = fields.Selection(related="communication_id.send_mode")
    send_state = fields.Selection(related="communication_id.state")
    body_html = fields.Html(compute="_compute_html")

    def _compute_preview(self):
        for wizard in self:
            comm = wizard.communication_id
            if wizard.state != "physical":
                wizard.preview = comm.body_html
                continue
            wizard.preview = (
                self.env["ir.actions.report"]
                .with_context(bin_size=False, lang=comm.partner_id.lang)
                ._render_qweb_html(comm.report_id.xml_id, comm.ids)[0]
            )

    def _compute_html(self):
        comm = self.communication_id
        template = getattr(comm.email_template_id, "sendgrid_localized_template", False)
        if template:
            body_html = template.html_content.replace("<%body%>", comm.body_html)
            self.body_html = body_html

        self.body_html = comm.body_html

    def send(self):
        return self.communication_id.send()
