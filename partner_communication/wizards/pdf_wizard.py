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

from openerp import models, api, fields


class PdfPreviewWizard(models.TransientModel):
    """
    Generate pdf of communication.
    """
    _name = 'partner.communication.pdf.wizard'

    fname = fields.Char(default='preview.pdf', readonly=True)
    pdf = fields.Binary(
        'Download the preview', default=lambda s: s._get_pdf(), readonly=True
    )
    state = fields.Char(default=lambda s: s._get_state())
    body_html = fields.Html(default=lambda s: s._get_html(), readonly=True)

    @api.model
    def _get_state(self):
        context = self.env.context
        comm = self.env[context['active_model']].browse(context['active_id'])
        return comm.send_mode

    @api.model
    def _get_pdf(self):
        context = self.env.context
        comm = self.env[context['active_model']].browse(context['active_id'])
        report_obj = self.env['report'].with_context(
            lang=comm.partner_id.lang, must_skip_send_to_printer=True)
        data = report_obj.get_pdf(comm, comm.report_id.report_name)
        return base64.b64encode(data)

    @api.model
    def _get_html(self):
        context = self.env.context
        comm = self.env[context['active_model']].browse(context['active_id'])
        template = comm.email_template_id.sendgrid_localized_template
        if template:
            body_html = template.html_content.replace(
                '<%body%>', comm.body_html)
            return body_html

        return comm.body_html
