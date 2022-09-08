##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import io

from PyPDF2 import PdfFileReader

from odoo import models, api, fields


class RevisionPreview(models.TransientModel):
    _name = "partner.communication.revision.preview"
    _description = "Communication revision preview"

    revision_id = fields.Many2one(
        "partner.communication.revision",
        readonly=True,
        required=True,
        ondelete="cascade",
    )
    state = fields.Selection(
        [("active_revision", "active"), ("working_revision", "working")]
    )
    name = fields.Char(related="revision_id.config_id.name", readonly=True)
    model = fields.Char(related="revision_id.model", readonly=True)
    model_desc = fields.Char(
        related="revision_id.config_id.model_id.name", readonly=True
    )
    res_id = fields.Reference(
        selection="_reference_models", default=lambda s: s._default_model()
    )
    preview_job_id = fields.Many2one("partner.communication.job", readonly=True)
    preview_html = fields.Html(related="preview_job_id.body_html")
    pdf_data = fields.Binary(readonly=True)
    pdf_name = fields.Char(default="letter_preview.pdf", readonly=True)
    pdf_page_count = fields.Integer("Number of pages", readonly=True)

    @api.model
    def _reference_models(self):
        revision_id = self._context.get("revision_id")
        if not revision_id:
            return []
        revision = self.env["partner.communication.revision"].browse(int(revision_id))
        domain = [("model", "=", revision.model)]
        models = self.env["ir.model"].search(domain)
        return [(model.model, model.name) for model in models]

    @api.model
    def _default_model(self):
        recs = self._reference_models()
        model = recs[0][0]
        criteria = (
            [("partner_id.lang", "=", self.env.lang)]
            if model != "res.partner"
            else [("lang", "=", self.env.lang)]
        )
        return model + "," + str(self.env[model].search(criteria, limit=1).id)

    def unlink(self):
        """ Remove preview jobs. """
        self.mapped("preview_job_id").unlink()
        return super().unlink()

    def preview(self):
        if not self.revision_id or not self.res_id:
            return self._reload()
        record = self.env[self.model].browse(int(self.res_id))
        partner_id = record.id if self.model == "res.partner" else record.partner_id.id
        config = self.revision_id.config_id
        job_vals = {
            "config_id": config.id,
            "object_ids": self.res_id.id,
            "partner_id": partner_id,
            "state": "done",  # Prevents sending test jobs,
            "send_mode": "digital",  # Prevents pdf generation
            "body_html": self._context.get("working_text"),  # Custom text
            "subject": self._context.get("working_subject"),
            "auto_send": False,  # Prevents automatic sending
            "lang": self.revision_id.lang,
        }
        if not self.preview_job_id:
            # Avoid creating attachments for the communication
            attachments_function = config.attachments_function
            if attachments_function:
                config.write({"attachments_function": False})
            # Create a test communication_job record
            self.preview_job_id = self.preview_job_id.create(job_vals)
            if attachments_function:
                config.write({"attachments_function": attachments_function})
        elif self.state == "active_revision":
            self.preview_job_id.write(job_vals)
            self.preview_job_id.with_context(
                {"lang_preview": job_vals["lang"]}
            ).quick_refresh()

        if config.report_id:
            # Create a PDF preview
            pdf_data = (
                config.report_id
                .with_context(must_skip_send_to_printer=True)
                ._render_qweb_pdf(self.preview_job_id.ids)
            )[0]
            pdf = PdfFileReader(io.BytesIO(pdf_data))
            self.write(
                {
                    "pdf_data": base64.b64encode(pdf_data),
                    "pdf_page_count": pdf.getNumPages(),
                }
            )
        return self._reload()

    def close(self):
        self.preview_job_id.sudo().unlink()
        return True

    def _reload(self):
        return {
            "context": self.env.context,
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.onchange("res_id")
    def _res_id_change(self):
        if self.res_id:
            self._reload()
