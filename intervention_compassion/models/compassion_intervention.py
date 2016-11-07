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

import logging

from openerp import models, fields, _, api
from openerp.addons.message_center_compassion.mappings import base_mapping \
     as mapping

logger = logging.getLogger(__name__)


class CompassionIntervention(models.Model):
    """ All interventions on hold or sponsored.
    """
    _inherit = ['compassion.generic.intervention', 'mail.thread']
    _name = 'compassion.intervention'
    _description = 'Intervention'

    # General Information
    #####################
    type = fields.Selection(store=True, readonly=True)
    parent_id = fields.Many2one(
        'compassion.intervention', help='Parent Intervention'
    )
    intervention_status = fields.Selection([
        ("Committed", _("Committed")),
        ("Fully Funded", _("Fully funded")),
        ("Inactive", _("Inactive")),
        ("On Hold", _("On hold")),
        ("Partially Committed", _("Partially committed")),
        ("Partially Funded", _("Partially funded")),
    ])
    funding_global_partners = fields.Char()
    service_level = fields.Selection([
        ("Level 1", _("Level 1")),
        ("Level 2", _("Level 2")),
        ("Level 3", _("Level 3")),
    ])
    cancel_reason = fields.Char()

    # Schedule Information
    ######################
    start_date = fields.Date(help='Actual start date')
    actual_duration = fields.Integer(
        help='Actual duration in months')
    initial_planned_end_date = fields.Date()
    planned_end_date = fields.Date()
    end_date = fields.Date(help='Actual end date')

    # Budget Information (all monetary fields are in US dollars)
    ####################
    estimated_local_contribution = fields.Float()
    impacted_beneficiaries = fields.Integer(
        help='Actual number of impacted beneficiaries')
    local_contribution = fields.Float(help='Actual local contribution')

    # Intervention Details Information
    ##################################
    problem_statement = fields.Text()
    background_information = fields.Text()
    objectives = fields.Text()
    success_factors = fields.Text()
    solutions = fields.Text()
    not_funded_implications = fields.Text()
    implementation_risks = fields.Text()

    # Service Level 3 Details
    #########################
    sla_negotiation_status = fields.Selection([
        ("FO Costs Proposed", _("FO Costs Proposed")),
        ("GP Accepted Costs", _("GP Accepted Costs")),
        ("GP Preferences Submitted", _("GP Preferences Submitted")),
        ("GP Rejected Costs", _("GP Rejected Costs")),
    ])
    sla_comments = fields.Char()
    fo_proposed_sla_costs = fields.Float(
        help='The costs proposed by the Field Office for the SLA')
    approved_sla_costs = fields.Float(
        help='The final approved Service Level Agreement Cost'
    )
    deliverable_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable_rel',
        'intervention_id', 'deliverable_id',
        string='Selected Deliverables'
    )

    @api.multi
    def get_infos(self):
        """ Get the most recent information about the intervention """
        message_obj = self.env['gmc.message.pool'].with_context(
            async_mode=False)
        action_id = self.env.ref(
            'intervention_compassion.intervention_details_request').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id,
        }
        message_obj.create(message_vals)
        return True

    # TODO: for incoming messages
    @api.model
    def process_commkit(self, commkit_data):
        """This function is automatically executed when a
        Message is received. It will convert the message from json to odoo
        format and then update the concerned records
        :param commkit_data contains the data of the message (json)
        :return list of intervention ids which are concerned by the
        message """
        intervention_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'intervention_mapping')
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        interventionDetailsRequest = commkit_data[
            'InterventionDetailsRequest']
        intervention_local_ids = []
        # For each dictionary, we update the corresponding record
        for idr in interventionDetailsRequest:
            vals = intervention_mapping.get_vals_from_connect(idr)
            intervention_id = vals['intervention_id']

            intervention = self.env['compassion.intervention'].search([
                ('intervention_id', '=like', intervention_id)
            ])

            intervention_local_ids.append(intervention.id)
            intervention.write(vals)

        return intervention_local_ids


class InterventionDeliverable(models.Model):
    _name = 'compassion.intervention.deliverable'
    _inherit = 'connect.multipicklist'

    res_model = 'compassion.intervention'
    res_field = 'deliverable_ids'
