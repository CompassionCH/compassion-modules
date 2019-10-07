
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class TemplatePreview(models.TransientModel):
    _inherit = "email_template.preview"

    res_id = fields.Reference(selection=lambda s: s._reference_models(),
                              default=lambda s: s._default_model())

    @api.model
    def _reference_models(self):
        template = self.env['mail.template'].browse(
            self._context.get('active_id')
        )
        domain = [('model', '=', template.model)]
        models = self.env['ir.model'].search(domain)
        result = [(model.model, model.name) for model in models]
        return result

    @api.model
    def _default_model(self):
        recs = self._reference_models()
        model = recs[0][0]
        model_obj = self.env[model]
        has_partner_field = hasattr(model_obj, 'partner_id')
        if has_partner_field:
            domain = [('partner_id', '!=', False)]
        else:
            domain = []
        result = model + ',' + str(model_obj.search(domain, limit=1).id)
        return result

    @api.onchange('res_id')
    @api.multi
    def on_change_res_id(self):
        return super(TemplatePreview, self).on_change_res_id()
