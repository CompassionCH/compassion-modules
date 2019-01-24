# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import StringIO
import base64

from pyPdf import PdfFileReader

from odoo import models, api, fields


class RevisionPreview(models.TransientModel):
    _name = 'partner.communication.revision.preview'
    _description = 'Communication revision preview'

    revision_id = fields.Many2one(
        'partner.communication.revision', readonly=True, required=True,
        ondelete='cascade'
    )
    state = fields.Selection([
        ('active_revision', 'active'),
        ('working_revision', 'working')
    ])
    name = fields.Char(related='revision_id.config_id.name', readonly=True)
    model = fields.Char(related='revision_id.model', readonly=True)
    model_desc = fields.Char(
        related='revision_id.config_id.model_id.name', readonly=True)
    res_id = fields.Selection(
        '_select_res_id', default=lambda s: s._default_res_id()
    )
    preview_job_id = fields.Many2one(
        'partner.communication.job', readonly=True)
    preview_html = fields.Html(related='preview_job_id.body_html')
    pdf_data = fields.Binary(readonly=True)
    pdf_name = fields.Char(default='letter_preview.pdf', readonly=True)
    pdf_page_count = fields.Integer('Number of pages', readonly=True)

    @api.model
    def _select_res_id(self):
        revision_id = self._context.get('revision_id')
        if not revision_id:
            return []
        revision = self.env['partner.communication.revision'].browse(
            int(revision_id))
        domain = []
        if revision.model == 'res.partner':
            domain.append(('lang', '=', revision.lang))
        else:
            domain.append(('partner_id.lang', '=', revision.lang))
        records = self.env[revision.model].search(domain, limit=10,
                                                  order='id desc')
        res = [(str(r[0]), r[1]) for r in records.name_get()]
        return res

    @api.model
    def _default_res_id(self):
        recs = self._select_res_id()
        return recs and recs[0][0]

    @api.multi
    def unlink(self):
        """ Remove preview jobs. """
        self.mapped('preview_job_id').unlink()
        return super(RevisionPreview, self).unlink()

    @api.multi
    def preview(self):
        if not self.revision_id or not self.res_id:
            return self._reload()
        record = self.env[self.model].browse(int(self.res_id))
        partner_id = record.id if self.model == 'res.partner' else \
            record.partner_id.id
        config = self.revision_id.config_id
        job_vals = {
            'config_id': config.id,
            'object_ids': self.res_id,
            'partner_id': partner_id,
            'state': 'done',  # Prevents sending test jobs,
            'send_mode': 'digital',  # Prevents pdf generation
            'body_html': self._context.get('working_text'),  # Custom text
            'subject': self._context.get('working_subject'),
            'auto_send': False,  # Prevents automatic sending
        }
        if not self.preview_job_id:
            # Avoid creating attachments for the communication
            attachments_function = config.attachments_function
            if attachments_function:
                config.write({'attachments_function': False})
            # Create a test communication_job record
            self.preview_job_id = self.preview_job_id.with_context(
                lang=self.revision_id.lang).create(job_vals)
            if attachments_function:
                config.write({'attachments_function': attachments_function})
        elif self.state == 'active_revision':
            self.preview_job_id.write(job_vals)
            self.preview_job_id.quick_refresh()

        if config.report_id:
            # Create a PDF preview
            pdf_data = self.env['report'].with_context(
                must_skip_send_to_printer=True
            ).get_pdf(self.preview_job_id.ids, config.report_id.report_name)
            pdf = PdfFileReader(StringIO.StringIO(pdf_data))
            self.write({
                'pdf_data': base64.b64encode(pdf_data),
                'pdf_page_count': pdf.getNumPages()
            })
        return self._reload()

    @api.multi
    def close(self):
        self.preview_job_id.sudo().unlink()
        return True

    def _reload(self):
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
