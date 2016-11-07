# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging

from openerp import models, fields, api, _

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
    name = fields.Char()
    intervention_id = fields.Char(required=True)
    field_office_id = fields.Many2one('compassion.field.office')
    icp_id = fields.Many2one('compassion.project')
    description = fields.Text()
    additional_marketing_information = fields.Text()
    category_id = fields.Many2one(
        'compassion.intervention.category', 'Category',
    )

    type = fields.Selection(related='category_id.type')
    subcategory_id = fields.Many2one(
        'compassion.intervention.subcategory', 'Subcategory',
    )
    funding_status = fields.Selection('get_funding_statuses')

    # Schedule Information
    ######################
    is_fo_priority = fields.Boolean('Is Field Office priority')
    proposed_start_date = fields.Date()
    start_no_later_than = fields.Date()
    expected_duration = fields.Integer(help='Expected duration in months')

    # Budget Information (all monetary fields are in US dollars)
    ####################
    currency_usd = fields.Many2one('res.currency', compute='_compute_usd')
    estimated_costs = fields.Float()
    remaining_amount_to_raise = fields.Float()
    pdc_costs = fields.Float(help='Program development costs')
    total_cost = fields.Float()
    estimated_impacted_beneficiaries = fields.Integer()

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
            'name', 'intervention_id', 'field_office_id', 'icp_id',
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
        rel_fields = ['field_office_id', 'icp_id', 'category_id',
                      'subcategory_id']
        for field in rel_fields:
            if vals.get(field):
                vals[field] = vals[field][0]

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

    parent_intervention = fields.Char()
    holding_partner_id = fields.Many2one(
        'compassion.global.partner', 'Major holding partner')
