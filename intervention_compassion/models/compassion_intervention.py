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

from openerp import models, fields, _

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
    intervention_status = fields.Selection([
        ("Committed", _("Committed")),
        ("Fully Funded", _("Fully funded")),
        ("Inactive", _("Inactive")),
        ("On Hold", _("On hold")),
        ("Partially Committed", _("Partially committed")),
        ("Partially Funded", _("Partially funded")),
    ])
    funding_global_partner_ids = fields.Many2many(
        'compassion.global.partner', 'compassion_gp_intervention_rel',
        'intervention_id', 'global_partner_id',
        'Funding Global Partners'
    )
    service_level = fields.Selection([
        ("Level 1", _("Level 1")),
        ("Level 2", _("Level 2")),
        ("Level 3", _("Level 3")),
    ])
    cancel_reason = fields.Char()

    # Schedule Information
    ######################
    start_date = fields.Date(help='Actual start date')
    expected_duration = fields.Integer(help='Expected duration in months')
    initial_planned_end_date = fields.Date()
    planned_end_date = fields.Date()
    end_date = fields.Date(help='Actual end date')

    # Budget Information (all monetary fields are in US dollars)
    ####################
    estimated_local_contribution = fields.Float()
    total_cost = fields.Float(help='Actual costs')
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
    fo_proposed_sla_costs = fields.Float(
        help='The costs proposed by the Field Office for the SLA')
    approved_sla_costs = fields.Float(
        help='The final approved Service Level Agreement Cost'
    )
    gp_interim_report_request = fields.Boolean()
    gp_final_report_request = fields.Boolean()
    deliverable_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable_rel',
        'intervention_id', 'deliverable_id',
        string='Selected Deliverables'
    )


class InterventionDeliverable(models.Model):
    _name = 'compassion.intervention.deliverable'
    _inherit = 'connect.multipicklist'

    res_model = 'compassion.intervention'
    res_field = 'deliverable_ids'
