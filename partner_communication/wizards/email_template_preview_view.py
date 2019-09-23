# -*- coding: utf-8 -*-
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
        return [(model.model, model.name) for model in models]

    @api.model
    def _default_model(self):
        recs = self._reference_models()
        model = recs[0][0]
        specific_domain = {
            'res.partner': []
        }
        domain = specific_domain.get(model, [('partner_id', '!=', False)])
        return model + ',' + str(self.env[model].search(domain, limit=1).id)
