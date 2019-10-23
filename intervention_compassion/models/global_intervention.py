##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class GlobalIntervention(models.TransientModel):
    """ Available child in the global childpool
    """
    _inherit = ['compassion.generic.intervention', 'compassion.mapped.model']
    _name = 'compassion.global.intervention'
    _description = 'Global Intervention'

    parent_intervention = fields.Char(readonly=True)
    amount_on_hold = fields.Float(compute='_compute_amount_on_hold')
    holding_partner_id = fields.Many2one(
        'compassion.global.partner', 'Major holding partner', readonly=True)
    can_be_funded = fields.Boolean(compute='_compute_can_be_funded')
    fcp_ids = fields.Many2many(
        'compassion.project', 'fcp_global_interventions', 'intervention_id',
        'fcp_id', string='FCPs', readonly=True
    )

    @api.multi
    def _compute_amount_on_hold(self):
        for intervention in self:
            intervention.amount_on_hold = \
                intervention.total_cost - \
                intervention.remaining_amount_to_raise

    @api.multi
    def _compute_can_be_funded(self):
        for intervention in self:
            intervention.can_be_funded = intervention.funding_status in (
                'Available', 'Partially Held', 'Partially Committed'
            ) and intervention.remaining_amount_to_raise > 0

    @api.multi
    def make_hold(self):
        return {
            'name': _('Intervention Hold Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'compassion.intervention.hold.wizard',
            'context': self.with_context({
                'default_intervention_id': self.id,
                'default_hold_amount': self.remaining_amount_to_raise,
            }).env.context,
            'target': 'new',
        }

    ##########################################################################
    #                              Mapping METHOD                            #
    ##########################################################################

    @api.multi
    def data_to_json(self, mapping_name=None):
        odoo_data = super().data_to_json(mapping_name)
        if 'category_id' in odoo_data and 'type' in odoo_data:
            category_obj = self.env['compassion.intervention.category']
            selected_category = category_obj.browse(odoo_data['category_id'])
            category = category_obj.search([
                ('name', '=', selected_category.name),
                ('type', '=', odoo_data['type'])
            ])
            odoo_data['category_id'] = category.id
            del odoo_data['type']
        return odoo_data

    @api.model
    def json_to_data(self, json, mapping_name=None):
        if 'ICP' in json:
            json['ICP'] = json['ICP'].split("; ")
        return super().json_to_data(json, mapping_name)
