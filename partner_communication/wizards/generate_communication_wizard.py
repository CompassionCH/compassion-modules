##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, api, fields, _
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class GenerateCommunicationWizard(models.TransientModel):
    _name = "partner.communication.generate.wizard"
    _description = "Partner Communication Generation Wizard"

    state = fields.Selection(
        [("edit", "edit"), ("preview", "preview"), ("generation", "generation")],
        default="edit",
    )
    selection_domain = fields.Char()
    partner_ids = fields.Many2many(
        "res.partner",
        string="Recipients",
        readonly=False,
        compute="_compute_partners"
    )
    force_language = fields.Selection("_lang_select")
    model_id = fields.Many2one(
        "partner.communication.config",
        "Template",
        domain=[("model", "=", "res.partner")],
        required=True
    )
    send_mode = fields.Selection("_send_mode_select")
    customize_template = fields.Boolean()
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
    @api.depends("selection_domain")
    def _compute_partners(self):
        if self.selection_domain:
            self.partner_ids = self.env["res.partner"].search(
                safe_eval(self.selection_domain)
            )

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

    def generate_communications(self, async_mode=True):
        """ Create the communication records """
        default = self.env.ref("partner_communication.default_communication")
        model = self.model_id or default
        for partner in self.partner_ids:
            vals = {
                "partner_id": partner.id,
                "object_ids": partner.id,
                "config_id": model.id,
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

    def create_communication(self, vals):
        """ Generate partner communication """
        communication = self.env["partner.communication.job"].create(vals)
        communication.print_header = self.print_header
        if self.force_language:
            model = self.model_id
            template = model.email_template_id.with_context(
                lang=self.force_language, salutation_language=self.force_language
            )
            new_subject = template._render_template(
                template.subject, "partner.communication.job", communication.ids
            )
            new_text = template._render_template(
                template.body_html, "partner.communication.job", communication.ids
            )
            communication.body_html = new_text[communication.id]
            communication.subject = new_subject[communication.id]

        self.communication_ids += communication
