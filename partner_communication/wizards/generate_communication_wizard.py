# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _
from odoo.tools import safe_eval
from odoo.addons.queue_job.job import job


class GenerateCommunicationWizard(models.TransientModel):
    _name = 'partner.communication.generate.wizard'

    state = fields.Selection([
        ('edit', 'edit'),
        ('preview', 'preview'),
        ('generation', 'generation')
    ], default='edit')
    selection_domain = fields.Char()
    partner_ids = fields.Many2many(
        'res.partner', string='Recipients',
        default=lambda s: s._default_partners()
    )
    force_language = fields.Selection('_lang_select')
    model_id = fields.Many2one(
        'partner.communication.config', 'Template',
        domain=[('model', '=', 'res.partner')]
    )
    send_mode = fields.Selection('_send_mode_select', default='physical')
    customize_template = fields.Boolean()
    subject = fields.Char()
    body_html = fields.Html()
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Letter template',
        domain=[('model', '=', 'partner.communication.job')]
    )
    language_added_in_domain = fields.Boolean()
    preview = fields.Html(readonly=True)
    communication_ids = fields.Many2many(
        'partner.communication.job', 'partner_communication_generation_rel',
        string='Communications')
    progress = fields.Float(compute='_compute_progress')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_partners(self):
        partners = self.env['res.partner'].browse(self.env.context.get(
            'active_ids', []))
        return partners.ids

    @api.model
    def _lang_select(self):
        languages = self.env['res.lang'].search([])
        return [(language.code, language.name) for language in languages]

    @api.model
    def _send_mode_select(self):
        return self.env['partner.communication.job'].send_mode_select()

    @api.multi
    def _compute_progress(self):
        for wizard in self:
            wizard.progress = float(len(wizard.communication_ids) * 100) / (
                len(wizard.partner_ids) or 1)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('selection_domain', 'force_language')
    def onchange_domain(self):
        if self.force_language and not self.language_added_in_domain:
            domain = self.selection_domain or '[]'
            domain = domain[:-1] + ", ('lang', '=', '{}')]".format(
                self.force_language)
            self.selection_domain = domain.replace('[, ', '[')
            self.language_added_in_domain = True
        if self.selection_domain:
            self.partner_ids = self.env['res.partner'].search(
                safe_eval(self.selection_domain))
        if not self.force_language:
            self.language_added_in_domain = False

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id:
            self.body_html = self.model_id.email_template_id.body_html
            self.subject = self.model_id.email_template_id.subject
            send_mode = self.model_id.send_mode.replace('auto_', '')
            if send_mode in [m[0] for m in self._send_mode_select()]:
                self.send_mode = send_mode

    @api.multi
    def get_preview(self):
        comm_model = 'partner.communication.job'
        config = self.model_id or self.env.ref(
            'partner_communication.default_communication')
        template = config.email_template_id
        model = template.model or comm_model
        res_preview = self.env[comm_model].create({
            'partner_id': self.partner_ids[0].id,
            'config_id': config.id,
            'object_ids': self.env.context.get('object_ids',
                                               self.partner_ids[0].id),
        })
        self.preview = template.render_template(
            self.body_html, model, res_preview.ids)[res_preview.id]
        res_preview.unlink()
        self.state = 'preview'
        return self.reload()

    @api.multi
    def edit(self):
        self.state = 'edit'
        return self.reload()

    @api.multi
    def generate(self):
        self.state = 'generation'
        self.with_delay().generate_communications()
        return self.reload()

    @api.multi
    def reload(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Communications'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': self._context,
            'target': 'new',
        }

    @api.multi
    def close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Communications'),
            'res_model': 'partner.communication.job',
            'domain': [('id', 'in', self.communication_ids.ids)],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': self._context,
        }

    @job
    def generate_communications(self):
        """ Create the communication records """
        default = self.env.ref('partner_communication.default_communication')
        model = self.model_id or default
        for partner in self.partner_ids:
            self.with_delay().create_communication({
                'partner_id': partner.id,
                'object_ids': partner.id,
                'config_id': model.id,
                'auto_send': False,
                'send_mode': self.send_mode,
                'report_id': self.report_id.id or model.report_id.id,
            })
        return True

    @job(default_channel='root.partner_communication')
    def create_communication(self, vals):
        """ Generate partner communication """
        communication = self.env['partner.communication.job'].create(vals)
        if self.customize_template or not self.model_id:
            default = self.env.ref(
                'partner_communication.default_communication')
            model = self.model_id or default
            template = model.email_template_id.with_context(
                lang=self.force_language or self.env.context.lang)
            new_subject = template.render_template(
                self.subject, 'partner.communication.job',
                communication.ids)
            new_text = template.render_template(
                self.body_html, 'partner.communication.job',
                communication.ids)
            communication.body_html = new_text[communication.id]
            communication.subject = new_subject[communication.id]

        self.communication_ids += communication
