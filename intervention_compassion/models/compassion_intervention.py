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
from openerp.exceptions import Warning
from openerp.addons.message_center_compassion.mappings import base_mapping \
     as mapping

logger = logging.getLogger(__name__)


class CompassionIntervention(models.Model):
    """ All interventions on hold or sponsored.
    """
    _inherit = ['compassion.generic.intervention', 'mail.thread']
    _name = 'compassion.intervention'
    _description = 'Intervention'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    # General Information
    #####################
    type = fields.Selection(store=True, readonly=True)
    parent_id = fields.Many2one(
        'compassion.intervention', help='Parent Intervention', readonly=True
    )
    intervention_status = fields.Selection([
        ("Committed", _("Committed")),
        ("Fully Funded", _("Fully funded")),
        ("Inactive", _("Inactive")),
        ("On Hold", _("On hold")),
        ("Partially Committed", _("Partially committed")),
        ("Partially Funded", _("Partially funded")),
        ("Approved", _("Approved")),
    ], readonly=True)
    funding_global_partners = fields.Char(readonly=True)
    service_level = fields.Selection([
        ("Level 1", _("Level 1")),
        ("Level 2", _("Level 2")),
        ("Level 3", _("Level 3")),
    ])
    cancel_reason = fields.Char(readonly=True)

    # Schedule Information
    ######################
    start_date = fields.Date(help='Actual start date', readonly=True)
    actual_duration = fields.Integer(
        help='Actual duration in months', readonly=True)
    initial_planned_end_date = fields.Date(readonly=True)
    planned_end_date = fields.Date(readonly=True)
    end_date = fields.Date(help='Actual end date', readonly=True)

    # Budget Information (all monetary fields are in US dollars)
    ####################
    estimated_local_contribution = fields.Float(readonly=True)
    impacted_beneficiaries = fields.Integer(
        help='Actual number of impacted beneficiaries', readonly=True)
    local_contribution = fields.Float(
        readonly=True, help='Actual local contribution')

    # Intervention Details Information
    ##################################
    problem_statement = fields.Text(readonly=True)
    background_information = fields.Text(readonly=True)
    objectives = fields.Text(readonly=True)
    success_factors = fields.Text(readonly=True)
    solutions = fields.Text(readonly=True)
    not_funded_implications = fields.Text(readonly=True)
    implementation_risks = fields.Text(readonly=True)

    # Service Level 3 Details
    #########################
    sla_negotiation_status = fields.Selection([
        ("FO Costs Proposed", _("FO Costs Proposed")),
        ("GP Accepted Costs", _("GP Accepted Costs")),
        ("GP Preferences Submitted", _("GP Preferences Submitted")),
        ("GP Rejected Costs", _("GP Rejected Costs")),
    ], readonly=True)
    sla_comments = fields.Char(readonly=True)
    fo_proposed_sla_costs = fields.Float(
        readonly=True,
        help='The costs proposed by the Field Office for the SLA')
    approved_sla_costs = fields.Float(
        readonly=True,
        help='The final approved Service Level Agreement Cost'
    )
    deliverable_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable_rel',
        'intervention_id', 'deliverable_id',
        string='Selected Deliverables'
    )

    # Hold information
    ##################
    hold_id = fields.Char(readonly=True)
    hold_amount = fields.Float()
    expiration_date = fields.Date()
    next_year_opt_in = fields.Boolean()
    primary_owner = fields.Many2one(
        'res.users', domain=[('share', '=', False)]
    )
    secondary_owner = fields.Char()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        intervention = super(CompassionIntervention, self).create(vals)
        intervention.get_infos()
        return intervention

    @api.multi
    def write(self, vals):
        """ Update hold if values are changed. """
        hold_fields = [
            'hold_amount', 'expiration_date', 'next_year_opt_in',
            'primary_owner', 'secondary_owner']
        update_hold = False
        for field in hold_fields:
            if field in vals:
                update_hold = True
                break
        res = super(CompassionIntervention, self).write(vals)
        if update_hold:
            self.update_hold()
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
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

    @api.multi
    def update_hold(self):
        action_id = self.env.ref(
            'intervention_compassion.intervention_update_hold_action').id
        message = self.env['gmc.message.pool'].with_context(
            async_mode=False).create({
                'action_id': action_id,
                'object_id': self.id
            })
        if message.state == 'failure':
            raise Warning(_('Hold not updated'), message.failure_reason)
        return True

    @api.multi
    def hold_sent(self, intervention_vals):
        """ Do nothing when hold is sent. """
        return True

    @api.multi
    def hold_cancelled(self, intervention_vals):
        """ Remove the intervention. """
        return self.sudo().unlink()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def get_infos(self):
        """ Get the most recent information about the intervention """
        action_id = self.env.ref(
            'intervention_compassion.intervention_details_request').id

        message_vals = {
            'action_id': action_id,
            'object_id': self.id,
        }
        message = self.env['gmc.message.pool'].create(message_vals)
        if message.state == 'failure':
            raise Warning(message.failure_reason)
        return True

    @api.multi
    def cancel_hold(self):
        action_id = self.env.ref(
            'intervention_compassion.intervention_cancel_hold_action').id
        message = self.env['gmc.message.pool'].with_context(
            async_mode=False).create({
                'action_id': action_id,
                'object_id': self.id
            })
        if message.state == 'failure':
            raise Warning(_('Hold not cancelled'), message.failure_reason)
        return True


class InterventionDeliverable(models.Model):
    _name = 'compassion.intervention.deliverable'
    _inherit = 'connect.multipicklist'

    res_model = 'compassion.intervention'
    res_field = 'deliverable_ids'
