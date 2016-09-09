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

from openerp import api, models, fields


class DemandPlanningSettings(models.TransientModel):
    """ Settings configuration for Demand Planning."""
    _name = 'demand.planning.settings'
    _inherit = 'res.config.settings'

    number_children_website = fields.Integer()
    number_children_ambassador = fields.Integer()
    days_allocate_before_event = fields.Integer()
    days_for_hold = fields.Integer(default=10)

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
    def set_days_for_hold(self):
        self.env['ir.config_parameter'].set_param(
            'crm_compassion.days_for_hold',
            str(self.days_for_hold))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        web = int(param_obj.get_param('crm_compassion.number_children_web'))
        ambassador = int(param_obj.get_param(
            'crm_compassion.number_children_ambassador'))
        days_event = int(param_obj.get_param(
            'crm_compassion.days_allocate_before_event'))
        days_for_hold = int(param_obj.get_param(
            'crm_compassion.days_for_hold'))
        return {
            'number_children_website': web,
            'number_children_ambassador': ambassador,
            'days_allocate_before_event': days_event,
            'days_for_hold': days_for_hold
        }
