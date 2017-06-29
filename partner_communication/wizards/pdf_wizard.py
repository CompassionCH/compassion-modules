# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)

try:
    from wand.image import Image
except ImportError:
    _logger.error('Please install wand to use PDF Previews')


class PdfPreviewWizard(models.TransientModel):
    """
    Generate pdf of communication.
    """
    _name = 'partner.communication.pdf.wizard'

    communication_id = fields.Many2one(
        'partner.communication.job', required=True)
    preview = fields.Binary(compute='_compute_pdf')
    state = fields.Char(compute='_compute_state')
    body_html = fields.Html(compute='_compute_html')

    @api.multi
    def _compute_state(self):
        comm = self.communication_id
        self.state = comm.send_mode

    @api.multi
    def _compute_pdf(self):
        if self.state != 'physical':
            return
        comm = self.communication_id
        report_obj = self.env['report'].with_context(
            lang=comm.partner_id.lang, must_skip_send_to_printer=True)
        data = report_obj.get_pdf(comm.ids, comm.report_id.report_name)
        with Image(blob=data) as pdf_image:
            preview = base64.b64encode(pdf_image.make_blob(format='jpeg'))

        self.preview = preview

    @api.multi
    def _compute_html(self):
        comm = self.communication_id
        template = getattr(comm.email_template_id,
                           'sendgrid_localized_template', False)
        if template:
            body_html = template.html_content.replace(
                '<%body%>', comm.body_html)
            self.body_html = body_html

        self.body_html = comm.body_html
