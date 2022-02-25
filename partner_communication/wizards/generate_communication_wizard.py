##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from odoo.addons.queue_job.job import job

from odoo import models, api, fields, _
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)

try:
    from wand.image import Image
except ImportError:
    _logger.warning("Please install wand to use PDF Previews")


class GenerateCommunicationWizard(models.TransientModel):
    _name = "partner.communication.generate.wizard"
    _description = "Partner Communication Generation Wizard"

    state = fields.Selection(
        [("edit", "edit"), ("preview", "preview"), ("generation", "generation")],
        default="edit",
    )
    selection_domain = fields.Char(default=lambda s: s._default_domain())
    partner_ids = fields.Many2many(
        "res.partner",
        string="Recipients",
        default=lambda s: s._default_partners(),
        readonly=False,
    )
    force_language = fields.Selection("_lang_select")
    model_id = fields.Many2one(
        "partner.communication.config",
        "Template",
        domain=[("model", "=", "res.partner")],
        readonly=False,
    )
    send_mode = fields.Selection("_send_mode_select")
    customize_template = fields.Boolean()
    subject = fields.Char()
    body_html = fields.Text()
    report_id = fields.Many2one(
        "ir.actions.report",
        "Letter template",
        domain=[("model", "=", "partner.communication.job")],
        default=lambda s: s._default_report(),
        readonly=False,
    )
    preview_email = fields.Html(readonly=True)
    preview_pdf = fields.Binary(readonly=True)
    communication_ids = fields.Many2many(
        "partner.communication.job",
        "partner_communication_generation_rel",
        string="Communications",
        readonly=False,
    )
    progress = fields.Float(compute="_compute_progress")

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def render_preview(self, communication):
        report = communication.report_id.with_context(must_skip_send_to_printer=True)
        data = report.render_qweb_pdf(communication.ids)
        with Image(blob=data[0]) as pdf_image:
            preview = base64.b64encode(pdf_image.make_blob(format="jpeg"))
        return preview

    @api.model
    def _default_report(self):
        return self.env["ir.actions.report"].search([])[0]

    @api.model
    def _default_domain(self):
        default_partners = self._default_partners()
        return (
            "[]"
            if len(default_partners) == 0
            else f"[('id', 'in', {default_partners})]"
        )

    @api.model
    def _default_partners(self):
        partners = self.env["res.partner"].browse(
            self.env.context.get("active_ids", [])
        )
        return partners.ids

    @api.model
    def _lang_select(self):
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]

    @api.model
    def _send_mode_select(self):
        return self.env["partner.communication.job"].send_mode_select()

    @api.multi
    def _compute_progress(self):
        for wizard in self:
            wizard.progress = float(len(wizard.communication_ids) * 100) / (
                len(wizard.partner_ids) or 1
            )

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange("selection_domain")
    def onchange_domain(self):
        if self.selection_domain:
            self.partner_ids = self.env["res.partner"].search(
                safe_eval(self.selection_domain)
            )

    @api.onchange("model_id", "force_language")
    def onchange_model_or_language(self):
        if self.model_id:
            config = self.model_id.email_template_id
            if self.force_language:
                config = config.with_context(lang=self.force_language)
            self.report_id = self.model_id.report_id
            self.subject = config.subject
            self.body_html = config.body_html

    @api.multi
    def get_preview(self):
        partner = self.partner_ids[0]
        config = self.model_id
        object_ids = self.env.context.get("object_ids", partner.id)
        comm_vals = {
            "partner_id": partner.id,
            "config_id": config.id,
            "object_ids": object_ids,
            "auto_send": False,
        }
        if self.send_mode:
            comm_vals["send_mode"] = self.send_mode
        comm = self.env["partner.communication.job"].create(comm_vals)

        if self.force_language:
            comm = comm.with_context(lang_preview=self.force_language)
            comm.refresh_text()

        if self.customize_template:
            comm.email_template_id.body_html = self.body_html
            comm.body_html = self.env["mail.compose.message"].get_generated_fields(
                comm.email_template_id, comm.ids)["body_html"]

        self.preview_email = comm.body_html
        if self.send_mode in ["physical", "both"]:
            self.preview_pdf = self.render_preview(comm)

        comm.unlink()
        self.state = "preview"
        return self.reload()

    @api.multi
    def edit(self):
        self.state = "edit"
        return self.reload()

    @api.multi
    def generate(self):
        self.state = "generation"
        if len(self.partner_ids) > 5:
            self.with_delay().generate_communications()
            return self.reload()
        else:
            self.generate_communications(async_mode=False)
            return self.close()

    @api.multi
    def reload(self):
        if not self.exists():
            return True
        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Communications"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "view_type": "form",
            "context": self._context,
            "target": "new",
        }

    @api.multi
    def close(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Communications"),
            "res_model": "partner.communication.job",
            "domain": [("id", "in", self.communication_ids.ids)],
            "view_mode": "tree,form",
            "view_type": "form",
            "context": self._context,
        }

    @job(default_channel="root.partner_communication")
    def generate_communications(self, async_mode=True):
        """ Create the communication records """
        default = self.env.ref("partner_communication.default_communication")
        model = self.model_id or default
        for partner in self.partner_ids:
            vals = {
                "partner_id": partner.id,
                "object_ids": partner.id,
                "config_id": model.id,
                "report_id": self.report_id.id or model.report_id.id,
            }
            if self.send_mode:
                vals.update({
                    "send_mode": self.send_mode,
                    "auto_send": False
                })
            if async_mode:
                self.with_delay().create_communication(vals)
            else:
                self.create_communication(vals)
        return True

    @job(default_channel="root.partner_communication")
    def create_communication(self, vals):
        """ Generate partner communication """
        communication = self.env["partner.communication.job"].create(vals)
        communication.print_header = self.print_header
        if self.customize_template or not self.model_id:
            default = self.env.ref("partner_communication.default_communication")
            model = self.model_id or default
            template = model.email_template_id.with_context(
                lang=self.force_language or self.env.context.lang
            )
            new_subject = template._render_template(
                self.subject, "partner.communication.job", communication.ids
            )
            new_text = template._render_template(
                self.body_html, "partner.communication.job", communication.ids
            )
            communication.body_html = new_text[communication.id]
            communication.subject = new_subject[communication.id]

        self.communication_ids += communication
