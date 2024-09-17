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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class GenerateCommunicationWizard(models.TransientModel):
    _name = "partner.communication.generate.wizard"
    _inherit = "partner.communication.defaults"
    _description = "Partner Communication Generation Wizard"

    state = fields.Selection(
        [("edit", "edit"), ("preview", "preview"), ("generation", "generation")],
        default="edit",
    )
    selection_domain = fields.Char(
        default=lambda s: f"[('id', 'in', {s.env.context.get('active_ids')})]"
    )
    partner_ids = fields.Many2many(
        "res.partner", string="Recipients", readonly=False, compute="_compute_partners"
    )
    force_language = fields.Selection("_lang_select")
    model_id = fields.Many2one(
        "partner.communication.config",
        "Template",
        domain=[("model", "=", "res.partner")],
        required=True,
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
    scheduled_date = fields.Datetime("Schedule generation")

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

    def _compute_progress(self):
        for wizard in self:
            if wizard.scheduled_date:
                wizard.progress = 1
            else:
                wizard.progress = float(len(wizard.communication_ids) * 100) / (
                    len(wizard.partner_ids) or 1
                )

    @api.constrains("scheduled_date")
    def check_eta(self):
        for wizard in self:
            if wizard.scheduled_date and wizard.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Schedule date must be in the future"))

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.depends("selection_domain")
    def _compute_partners(self):
        if self.selection_domain:
            self.partner_ids = self.env["res.partner"].search(
                safe_eval(self.selection_domain)
            )

    def generate(self):
        self.state = "generation"
        if len(self.partner_ids) > 5:
            self.with_delay().generate_communications()
            return self.reload()
        else:
            self.generate_communications(async_mode=False)
            return self.close()

    def reload(self):
        if not self.exists():
            return True
        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Communications"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "context": self._context,
            "target": "new",
        }

    def close(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Communications"),
            "res_model": "partner.communication.job",
            "domain": [("id", "in", self.communication_ids.ids)],
            "view_mode": "tree,form",
            "context": self._context,
        }

    def generate_communications(self, async_mode=True):
        """Create the communication records"""
        processed_addresses = set()
        send_mode = self.send_mode or self.model_id.send_mode
        for partner in self.partner_ids:
            address = (
                partner.email
                if "digital" in send_mode
                else f"{partner.zip} {partner.city}"
            )
            if address in processed_addresses:
                continue
            processed_addresses.add(address)
            vals = {
                "partner_id": partner.id,
                "object_ids": partner.id,
                "config_id": self.model_id.id,
            }
            if self.send_mode:
                vals.update({"send_mode": self.send_mode, "auto_send": False})
            options = {
                "force_language": self.force_language,
            }
            if async_mode or self.scheduled_date:
                self.with_delay(
                    eta=self.scheduled_date, priority=50
                ).create_communication(vals, options)
            else:
                self.create_communication(vals, options)
        return True

    @api.model
    def create_communication(self, vals, options):
        """Generate partner communication"""
        communication = self.env["partner.communication.job"].create(vals)
        force_language = options.get("force_language")
        if force_language:
            template = communication.email_template_id.with_context(
                lang=force_language, salutation_language=force_language
            )
            new_subject = template._render_template(
                template.subject, "partner.communication.job", communication.ids
            )
            new_text = template._render_template(
                template.body_html, "partner.communication.job", communication.ids
            )
            communication.body_html = new_text[communication.id]
            communication.subject = new_subject[communication.id]

        if self.exists():
            self.communication_ids += communication
        return communication
