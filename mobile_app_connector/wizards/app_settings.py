# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class DemandPlanningSettings(models.TransientModel):
    _name = 'mobile.app.settings'
    _inherit = 'res.config.settings'

    default_s2b_template_id = fields.Many2one(
        'correspondence.template', 'Default S2B template', readonly=False)

    @api.multi
    def set_default_s2b_template_id(self):
        self.env['ir.config_parameter'].set_param(
            'mobile_app_connector.s2b_template',
            str(self.default_s2b_template_id.id))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        s2b_template_id = int(param_obj.get_param(
            'mobile_app_connector.s2b_template', '0'))
        all_values = {
            'default_s2b_template_id': s2b_template_id,
        }

        return {key: all_values.get(key, 0) for key in _fields}

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
