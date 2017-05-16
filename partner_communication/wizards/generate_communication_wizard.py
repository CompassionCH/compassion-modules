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
from openerp import models, api, fields, _


class GenerateCommunicationWizard(models.TransientModel):
    _name = 'partner.communication.generate.wizard'

    state = fields.Selection(
        [('edit', 'edit'), ('preview', 'preview')], default='edit'
    )
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
    preview = fields.Html(readonly=True)

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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('selection_domain', 'force_language')
    def onchange_domain(self):
        if self.force_language:
            domain = self.selection_domain or '[]'
            domain = domain[:-1] + ", ('lang', '=', '{}')]".format(
                self.force_language)
            self.selection_domain = domain.replace('[, ', '[')
        if self.selection_domain:
            self.partner_ids = self.env['res.partner'].search(
                eval(self.selection_domain))

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
        communication = self.model_id or self.env.ref(
            'partner_communication.default_communication')
        template = communication.email_template_id
        self.preview = template.render_template_batch(
            self.body_html, template.model, communication.ids)[
            communication.id]
        self.state = 'preview'
        return self._reload()

    @api.multi
    def edit(self):
        self.state = 'edit'
        return self._reload()

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def generate(self):
        comm_obj = self.env['partner.communication.job']
        communications = comm_obj
        default = self.env.ref('partner_communication.default_communication')
        model = self.model_id or default
        for partner in self.partner_ids:
            comm = comm_obj.create({
                'partner_id': partner.id,
                'object_ids': partner.id,
                'config_id': model.id,
                'auto_send': False,
                'send_mode': self.send_mode,
            })
            communications += comm

        if self.customize_template or not self.model_id:
            template = model.email_template_id
            new_texts = template.render_template_batch(
                self.body_html, template.model, communications.ids)
            new_subjects = template.render_template_batch(
                self.subject, template.model, communications.ids)
            for comm in communications:
                comm.body_html = new_texts[comm.id]
                comm.subject = new_subjects[comm.id]

        return {
            'name': _('Communications'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': comm_obj._name,
            'context': self.env.context,
            'domain': [('id', 'in', communications.ids)]
        }
