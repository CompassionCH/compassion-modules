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
    state = fields.Selection([
        ('on_hold', _('On Hold')),
        ('sla', _('SLA Negotiation')),
        ('committed', _('Committed')),
        ('active', _('Active')),
        ('close', _('Closed')),
        ('cancel', _('Cancelled')),
    ], default='on_hold', track_visibility='onchange')
    type = fields.Selection(store=True, readonly=True)
    parent_id = fields.Many2one(
        'compassion.intervention', help='Parent Intervention', readonly=True
    )
    intervention_status = fields.Selection([
        ("Approved", _("Approved")),
        ("Cancelled", _("Cancelled")),
        ("Closed", _("Closed")),
        ("Draft", _("Draft")),
        ("Rejected", _("Rejected")),
        ("Submitted", _("Submitted")),
    ], readonly=True)
    funding_global_partners = fields.Char(readonly=True)
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
    commitment_amount = fields.Float(readonly=True)

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
        ("--None--", _("None")),
        ("FO Costs Proposed", _("FO Costs Proposed")),
        ("GP Accepted Costs", _("GP Accepted Costs")),
        ("GP Preferences Submitted", _("GP Preferences Submitted")),
        ("GP Rejected Costs", _("GP Rejected Costs")),
    ], readonly=True, track_visibility='onchange')
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
        string='Selected Deliverables', readonly=True
    )
    sla_selection_complete = fields.Boolean()

    # Hold information
    ##################
    hold_id = fields.Char(readonly=True)
    service_level = fields.Selection([
        ("Level 1", _("Level 1")),
        ("Level 2", _("Level 2")),
        ("Level 3", _("Level 3")),
    ], required=True, readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    hold_amount = fields.Float(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    expiration_date = fields.Date(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    next_year_opt_in = fields.Boolean(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    primary_owner = fields.Many2one(
        'res.users', domain=[('share', '=', False)], readonly=True, states={
            'on_hold': [('readonly', False)],
            'sla': [('readonly', False)],
        })
    secondary_owner = fields.Char(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if vals.get('service_level') != 'Level 1':
            vals['state'] = 'sla'
        intervention = super(CompassionIntervention, self).create(vals)
        intervention.get_infos()
        return intervention

    @api.multi
    def write(self, vals):
        """
        When record is updated :

        - Update hold if values are changed.
        - Check SLA Negotiation modifications
        - Check start of intervention
        - Check end of intervention
        """
        hold_fields = [
            'hold_amount', 'expiration_date', 'next_year_opt_in',
            'primary_owner', 'secondary_owner', 'service_level']
        update_hold = False
        for field in hold_fields:
            if field in vals:
                update_hold = self.env.context.get('hold_update', True)
                break

        # Check SLA change
        service_level = vals.get('service_level')
        if service_level == 'Level 1':
            vals['state'] = 'on_hold'

        res = super(CompassionIntervention, self).write(vals)

        if update_hold:
            self.update_hold()

        # Check SLA Negotiation Status
        check_sla = self.filtered(lambda i: i.state in ('on_hold', 'sla'))
        sla_done = check_sla.filtered(
            lambda i: i.sla_selection_complete and (
                i.service_level == 'Level 2' or
                i.sla_negotiation_status == 'GP Accepted Costs')
        )
        super(CompassionIntervention, sla_done).write({'state': 'on_hold'})
        if service_level != 'Level 1':
            sla_wait = check_sla - sla_done
            super(CompassionIntervention, sla_wait).write({'state': 'sla'})

        # Check start of Intervention
        today = fields.Date.today()
        start = vals.get('start_date')
        if start and start < today:
            super(
                CompassionIntervention,
                self.filtered(lambda i: i.state == 'committed')).write({
                    'state': 'active'
                })

        # Check closure of Intervention
        intervention_status = vals.get('intervention_status')
        if intervention_status in ('Cancelled', 'Closed'):
            state = 'close' if intervention_status == 'Closed' else 'cancel'
            super(CompassionIntervention, self).write({'state': state})

        return res

    @api.multi
    def unlink(self):
        """ Only allow to delete cancelled Interventions. """
        if self.filtered(lambda i: i.state != 'cancel'):
            raise Warning(_("You can only delete cancelled Interventions."))
        return super(CompassionIntervention, self).unlink()

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
        """ Remove the hold and put intervention in Cancel state. """
        return self.write({
            'hold_id': False,
            'state': 'cancel',
        })

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
        message = self.env['gmc.message.pool'].with_context(
            hold_update=False).create(message_vals)
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

    @api.multi
    def create_commitment(self):
        self.ensure_one()
        return {
            'name': _('Intervention Commitment Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'compassion.intervention.commitment.wizard',
            'context': self.with_context({
                'default_intervention_id': self.id,
                'default_commitment_amount': self.hold_amount,
            }).env.context,
            'target': 'new',
        }


class InterventionDeliverable(models.Model):
    _name = 'compassion.intervention.deliverable'
    _inherit = 'connect.multipicklist'

    res_model = 'compassion.intervention'
    res_field = 'deliverable_ids'
