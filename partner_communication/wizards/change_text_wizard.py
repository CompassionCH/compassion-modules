
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ChangeTextWizard(models.TransientModel):
    _name = 'partner.communication.change.text.wizard'

    template_text = fields.Text(default=lambda s: s._default_text())
    state = fields.Char(default='edit')
    preview = fields.Html(readonly=True)

    @api.model
    def _default_text(self):
        context = self.env.context
        communications = self.env[context['active_model']].browse(
            context['active_ids'])
        config = communications.mapped('config_id')
        lang = list(set(communications.mapped('partner_id.lang')))
        if len(config) != 1:
            raise UserError(_("You can only update text "
                              "on one communication type at time."))
        if len(lang) != 1:
            raise UserError(
                _("Please update only one language at a time."))

        return config.email_template_id.with_context(lang=lang[0]).body_html

    @api.multi
    def update(self):
        """ Refresh the texts of communications given the new template. """
        self.ensure_one()
        context = self.env.context
        communications = self.env[context['active_model']].browse(
            context['active_ids'])
        config = communications.mapped('config_id')
        lang = communications[0].partner_id.lang
        template = config.email_template_id.with_context(lang=lang)
        if len(config) != 1:
            raise UserError(
                _("You can only update text on one communication "
                  "type at time."))
        new_texts = template.render_template(
            self.template_text,
            template.model, communications.ids)
        for comm in communications:
            comm.body_html = new_texts[comm.id]

        return True

    @api.multi
    def get_preview(self):
        context = self.env.context
        communication = self.env[context['active_model']].browse(
            context['active_id'])
        template = communication.email_template_id
        self.preview = template.render_template(
            self.template_text, template.model, communication.ids)[
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
