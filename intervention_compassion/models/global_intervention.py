# -*- coding: utf-8 -*-
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


class GenericIntervention(models.AbstractModel):
    """ Generic information of interventions shared by subclasses:
        - compassion.intervention : funded interventions
        - compassion.global.intervention : available interventions in global
                                           pool
    """
    _name = 'compassion.generic.intervention'

    # General Information
    #####################
    name = fields.Char(readonly=True)
    intervention_id = fields.Char(required=True, readonly=True)
    field_office_id = fields.Many2one('compassion.field.office',
                                      'Field Office', readonly=True)
    description = fields.Text(readonly=True)
    additional_marketing_information = fields.Text(readonly=True)
    category_id = fields.Many2one(
        'compassion.intervention.category', 'Category', readonly=True
    )

    type = fields.Selection(related='category_id.type')
    subcategory_id = fields.Many2one(
        'compassion.intervention.subcategory', 'Subcategory', readonly=True
    )
    funding_status = fields.Selection('get_funding_statuses', readonly=True)

    # Schedule Information
    ######################
    is_fo_priority = fields.Boolean('Is Field Office priority', readonly=True)
    proposed_start_date = fields.Date(readonly=True)
    start_no_later_than = fields.Date(readonly=True)
    expected_duration = fields.Integer(
        readonly=True, help='Expected duration in months')

    # Budget Information (all monetary fields are in US dollars)
    ####################
    currency_usd = fields.Many2one('res.currency', compute='_compute_usd')
    estimated_costs = fields.Float(readonly=True)
    remaining_amount_to_raise = fields.Float(readonly=True)
    pdc_costs = fields.Float(help='Program development costs', readonly=True)
    total_cost = fields.Float(readonly=True)
    requested_additional_funding = fields.Float(readonly=True)
    estimated_impacted_beneficiaries = fields.Integer(readonly=True)

    @api.model
    def get_funding_statuses(self):
        return [
            ("Available", _("Available")),
            ("Partially Held", _("Partially held")),
            ("Fully Held", _("Fully held")),
            ("Partially Committed", _("Partially committed")),
            ("Fully Committed", _("Fully committed")),
            ("Inactive", _("Inactive")),
            ("Ineligible", _("Ineligible")),
        ]

    @api.model
    def get_fields(self):
        return [
            'name', 'intervention_id', 'field_office_id', 'fcp_ids',
            'description', 'additional_marketing_information', 'category_id',
            'subcategory_id', 'funding_status', 'is_fo_priority',
            'proposed_start_date', 'start_no_later_than', 'estimated_costs',
            'estimated_impacted_beneficiaries', 'remaining_amount_to_raise',
            'pdc_costs', 'total_cost'
        ]

    def get_vals(self):
        """ Get the required field values of one record for other record
            creation.
            :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        rel_fields = ['field_office_id', 'category_id', 'subcategory_id']
        for field in rel_fields:
            if vals.get(field):
                vals[field] = vals[field][0]

        fcp_ids = vals.get('fcp_ids')
        if fcp_ids:
            vals['fcp_ids'] = [(6, 0, fcp_ids)]

        del vals['id']
        return vals

    def _compute_usd(self):
        for intervention in self:
            intervention.currency_usd = self.env.ref('base.USD')


class GlobalIntervention(models.TransientModel):
    """ Available child in the global childpool
    """
    _inherit = 'compassion.generic.intervention'
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
