##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class DemandPlanningSettings(models.TransientModel):
    """ Settings configuration for Demand Planning."""
    _inherit = 'res.config.settings'

    number_children_website = fields.Integer()
    number_children_ambassador = fields.Integer()
    days_allocate_before_event = fields.Integer()
    days_hold_after_event = fields.Integer()

    @api.multi
    def set_number_children_website(self):
        self.env['ir.config_parameter'].set_param(
            'crm_compassion.number_children_web',
            str(self.number_children_website))

    @api.multi
    def set_number_children_ambassador(self):
        self.env['ir.config_parameter'].set_param(
            'crm_compassion.number_children_ambassador',
            str(self.number_children_ambassador))

    @api.multi
    def set_days_allocate_before_event(self):
        self.env['ir.config_parameter'].set_param(
            'crm_compassion.days_allocate_before_event',
            str(self.days_allocate_before_event))

    @api.multi
    def set_days_hold_after_event(self):
        self.env['ir.config_parameter'].set_param(
            'crm_compassion.days_hold_after_event',
            str(self.days_hold_after_event))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        web = int(param_obj.get_param(
            'crm_compassion.number_children_web', '500'))
        ambassador = int(param_obj.get_param(
            'crm_compassion.number_children_ambassador', '10'))
        days_event = int(param_obj.get_param(
            'crm_compassion.days_allocate_before_event', '10'))
        days_hold_after_event = int(param_obj.get_param(
            'crm_compassion.days_hold_after_event', '10'))

        all_values = {
            'number_children_website': web,
            'number_children_ambassador': ambassador,
            'days_allocate_before_event': days_event,
            'days_hold_after_event': days_hold_after_event
        }

        return {key: all_values.get(key, 10) for key in _fields}

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
