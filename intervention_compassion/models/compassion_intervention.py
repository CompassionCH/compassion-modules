##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import time

from odoo import models, fields, _, api
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

INTERVENTION_PORTAL_URL = "https://compassion.force.com/GlobalPartners/"


class CompassionIntervention(models.Model):
    """ All interventions on hold or sponsored.
    """
    _inherit = ['compassion.generic.intervention', 'mail.thread',
                'compassion.mapped.model']
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
    parent_intervention_name = fields.Char(string='Parent Intervention',
                                           readonly=True)
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
    fcp_ids = fields.Many2many(
        'compassion.project', 'fcp_interventions', 'intervention_id', 'fcp_id',
        string='FCPs', readonly=True,
    )
    product_template_id = fields.Many2one('product.template', 'Linked product')

    # Multicompany
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id.id
    )

    # Schedule Information
    ######################
    start_date = fields.Date(help='Actual start date', readonly=True)
    actual_duration = fields.Integer(
        help='Actual duration in months', readonly=True)
    initial_planned_end_date = fields.Date(readonly=True)
    planned_end_date = fields.Date(
        readonly=True, track_visibility='onchange')
    end_date = fields.Date(
        help='Actual end date', readonly=True, track_visibility='onchange')

    # Budget Information (all monetary fields are in US dollars)
    ####################
    estimated_local_contribution = fields.Float(readonly=True)
    impacted_beneficiaries = fields.Integer(
        help='Actual number of impacted beneficiaries', readonly=True)
    local_contribution = fields.Float(
        readonly=True, help='Actual local contribution')
    commitment_amount = fields.Float(
        readonly=True, track_visibility='onchange')
    commited_percentage = fields.Float(
        readonly=True, track_visibility='onchange', default=100.0)
    total_expense = fields.Char(
        'Total expense', compute='_compute_move_line', readonly=True)
    total_income = fields.Char(
        'Total income', compute='_compute_move_line', readonly=True)
    total_amendment = fields.Float()
    total_actual_cost_local = fields.Float(
        'Total cost (local currency)'
    )
    total_estimated_cost_local = fields.Float(
        'Estimated costs (local currency)'
    )
    local_currency_id = fields.Many2one('res.currency',
                                        related='field_office_id.country_id.'
                                                'currency_id')

    # Intervention Details Information
    ##################################
    problem_statement = fields.Text(readonly=True)
    background_information = fields.Text(readonly=True)
    objectives = fields.Text(readonly=True)
    success_factors = fields.Text(readonly=True)
    solutions = fields.Text(readonly=True)
    not_funded_implications = fields.Text(readonly=True)
    implementation_risks = fields.Text(readonly=True)

    # Service Level Negotiation
    ###########################
    sla_negotiation_status = fields.Selection([
        ("--None--", _("None")),
        ("FO Costs Proposed", _("FO Costs Proposed")),
        ("GP Accepted Costs", _("GP Accepted Costs")),
        ("GP Preferences Submitted", _("GP Preferences Submitted")),
        ("GP Rejected Costs", _("GP Rejected Costs")),
        ("FO Rejected GP Preferences", _("FO Rejected GP Preferences"))
    ], readonly=True, track_visibility='onchange')
    sla_comments = fields.Char(readonly=True)
    fo_proposed_sla_costs = fields.Float(
        readonly=True,
        help='The costs proposed by the Field Office for the SLA')
    approved_sla_costs = fields.Float(
        readonly=True,
        help='The final approved Service Level Agreement Cost'
    )
    deliverable_level_1_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable1_rel',
        'intervention_id', 'deliverable_id',
        string='Level 1 Deliverables',
        compute='_compute_level1_deliverables'
    )
    deliverable_level_2_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable2_rel',
        'intervention_id', 'deliverable_id',
        string='Level 2 Deliverables', readonly=True
    )
    deliverable_level_3_ids = fields.Many2many(
        'compassion.intervention.deliverable',
        'compassion_intervention_deliverable3_rel',
        'intervention_id', 'deliverable_id',
        string='Level 3 Deliverables', readonly=True
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
    }, track_visibility='onchange')
    expiration_date = fields.Date(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    next_year_opt_in = fields.Boolean(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })
    user_id = fields.Many2one(
        'res.users', 'Primary owner',
        domain=[('share', '=', False)], readonly=True, states={
            'on_hold': [('readonly', False)],
            'sla': [('readonly', False)],
        },
        track_visibility='onchange',
        oldname='primary_owner'
    )
    secondary_owner = fields.Char(readonly=True, states={
        'on_hold': [('readonly', False)],
        'sla': [('readonly', False)],
    })

    # Survival Information
    ######################
    survival_slots = fields.Integer(readonly=True)
    launch_reason = fields.Char(readonly=True)
    mother_children_challenges = fields.Char(
        'Challenges for mother and children', readonly=True
    )
    community_benefits = fields.Char(readonly=True)
    mother_average_age = fields.Integer(
        'Avg age of first-time mother', readonly=True)
    household_children_average = fields.Integer(
        'Avg of children per household', readonly=True
    )
    under_five_population = fields.Char(
        '% population under age 5', readonly=True
    )
    birth_medical = fields.Char(
        '% births in medical facility', readonly=True
    )
    spiritual_activity_ids = fields.Many2many(
        'fcp.spiritual.activity', 'intervention_spiritual_activities',
        string='Spiritual activities', readonly=True
    )
    cognitive_activity_ids = fields.Many2many(
        'fcp.cognitive.activity', 'intervention_cognitive_activities',
        string='Cognitive activities', readonly=True
    )
    physical_activity_ids = fields.Many2many(
        'fcp.physical.activity', 'intervention_physical_activities',
        string='Physical activities', readonly=True
    )
    socio_activity_ids = fields.Many2many(
        'fcp.sociological.activity', 'intervention_socio_activities',
        string='Sociological activities', readonly=True
    )
    activities_for_parents = fields.Char(readonly=True)
    other_activities = fields.Char(readonly=True)

    @api.multi
    def _compute_level1_deliverables(self):
        for intervention in self.filtered('type'):
            if 'CIV' in intervention.type:
                intervention.deliverable_level_1_ids = self.env.ref(
                    'intervention_compassion.deliverable_final_program_report')
            elif 'Survival' in intervention.type:
                intervention.deliverable_level_1_ids = self.env.ref(
                    'intervention_compassion.deliverable_icp_profile'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_survival_quarterly_report_data'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_survival_activity_report_lite'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_survival_launch_budget'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_survival_community_information'
                )
            elif 'Sponsorship' in intervention.type:
                intervention.deliverable_level_1_ids = self.env.ref(
                    'intervention_compassion.deliverable_icp_profile'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_icp_community_information'
                ) + self.env.ref(
                    'intervention_compassion.'
                    'deliverable_sponsorship_launch_budget'
                )

    def _compute_move_line(self):
        for record in self:
            mv_line_expense = record.env['account.move.line'].search(
                [('product_id.product_tmpl_id', '=',
                  record.product_template_id.id),
                 ('debit', '>', 0),
                 ('account_id', '=',
                  record.product_template_id.property_account_expense_id.id)
                 ])
            mv_line_income = record.env['account.move.line'].search(
                [('product_id.product_tmpl_id', '=',
                  record.product_template_id.id),
                 ('credit', '>', 0),
                 ('account_id', '=',
                  record.product_template_id.property_account_income_id.id)
                 ])

            total_inc = sum(mv_line_income.mapped('credit'))
            total_exp = sum(mv_line_expense.mapped('debit'))
            record.total_income = f'{total_inc} CHF'
            record.total_expense = f"{total_exp} CHF"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if vals.get('service_level') != 'Level 1':
            vals['state'] = 'sla'
        vals['commited_percentage'] = 0
        intervention = super().create(vals)
        intervention.get_infos()
        intervention.fcp_ids.get_lifecycle_event()
        return intervention

    @api.multi
    def write(self, vals):
        """
        When record is updated :

        - Update hold if values are changed.
        - Check SLA Negotiation modifications (in ir.action.rules)
        - Check end of intervention
        """
        hold_fields = [
            'hold_amount', 'expiration_date', 'next_year_opt_in',
            'user_id', 'secondary_owner', 'service_level']
        update_hold = False
        for field in hold_fields:
            if field in vals:
                update_hold = self.env.context.get('hold_update', True)
                break

        res = super().write(vals)

        if update_hold:
            self.update_hold()

        # Check closure of Intervention
        intervention_status = vals.get('intervention_status')
        if intervention_status in ('Cancelled', 'Closed'):
            state = 'close' if intervention_status == 'Closed' else 'cancel'
            super().write({'state': state})

        return res

    @api.multi
    def unlink(self):
        """ Only allow to delete cancelled Interventions. """
        if self.filtered(lambda i: i.state != 'cancel'):
            raise UserError(_("You can only delete cancelled Interventions."))
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_intervention(self, commkit_data):
        intervention_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'intervention_mapping')

        # Two messages can call this method. Try to find which one.
        intervention_details_request = commkit_data.get(
            'GPInitiatedInterventionHoldNotification',
            commkit_data.get('InterventionOptInHoldNotification')
        )

        intervention = self
        if intervention_details_request:
            vals = intervention_mapping.get_vals_from_connect(
                intervention_details_request)

            vals['total_cost'] = vals['hold_amount'] = float(
                vals['hold_amount'].replace("'", "").replace(",", ""))
            if not vals['secondary_owner']:
                del vals['secondary_owner']

            if 'service_level' not in vals:
                vals['service_level'] = 'Level 1'

            intervention_name = vals['name']

            if intervention_name.find('FY') != -1:
                split_name = intervention_name.split('FY')
                search_value = split_name[0] + 'FY' + str(int(split_name[1])-1)
                last_intervention = self.search([
                    ('name', '=', search_value)
                ])
                if last_intervention:
                    vals['product_template_id'] = \
                        last_intervention.product_template_id.id

            # By default we want to opt-in for next years
            vals['next_year_opt_in'] = True
            intervention = self.create(vals)

        return intervention.ids

    @api.model
    def update_intervention_details_request(self, commkit_data):
        """This function is automatically executed when a
        UpdateInterventionDetailsRequest Message is received. It will
        convert the message from json to odoo format and then update the
        concerned records
        :param commkit_data contains the data of the
        message (json)
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

            intervention = self.search([
                ('intervention_id', '=', intervention_id)
            ])
            if intervention:
                intervention_local_ids.append(intervention.id)
                intervention.with_context(hold_update=False).write(vals)
                intervention.message_post(_("The information of this "
                                          "intervention have been updated"),
                                          subject=(_(intervention.name +
                                                   "got an Update")),
                                          message_type='email',
                                          subtype='mail.mt_comment')

        return intervention_local_ids

    @api.multi
    def update_hold(self):
        action_id = self.env.ref(
            'intervention_compassion.intervention_update_hold_action').id
        message = self.env['gmc.message'].with_context(
            async_mode=False).create({
                'action_id': action_id,
                'object_id': self.id
            })
        if message.state == 'failure':
            raise UserError(message.failure_reason)
        return True

    @api.multi
    def hold_sent(self, intervention_vals=None):
        """ Do nothing when hold is sent. """
        return True

    @api.multi
    def hold_cancelled(self, intervention_vals=None):
        """ Remove the hold and put intervention in Cancel state. """
        self.write({
            'hold_id': False,
            'state': 'cancel',
        })
        self.message_post(
            body=_(f"The hold of {self.name} ({self.intervention_id}) was just cancelled."),
            subject=_("Intervention hold cancelled"),
            partner_ids=self.message_partner_ids.ids,
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )

    @api.model
    def auto_subscribe(self):
        """
        Method added to auto subscribe users after migration
        """
        interventions = self.search([
            ('user_id', '!=', False)
        ])
        for intervention in interventions:
            vals = {'user_id': intervention.user_id.id}
            intervention.message_auto_subscribe(['user_id'], vals)
        return True

    @api.model
    def commited_percent_change(self, commkit_data):
        """
        Called when GMC message received
        :param commkit_data: json data
        :return: list of ids updated
        """
        json_data = commkit_data.get(
            'InterventionCommittedPercentChangeNotification')
        intervention_id = json_data.get("Intervention_ID")
        intervention = self.search([
            ('intervention_id', '=', intervention_id)
        ])
        if intervention:
            intervention.commited_percentage = json_data.get(
                "CommittedPercent", 100)
            intervention.message_post(
                _("The commitment percentage has changed."),
                message_type='email', subtype='mail.mt_comment'
            )
        return intervention.ids

    @api.multi
    def link_product(self):
        # search existing project or create a new one if doesn't exist.
        for intervention in self:
            if intervention.product_template_id or \
                    intervention.state != 'committed' or not \
                    intervention.parent_intervention_name:
                continue
            product_name = intervention.parent_intervention_name
            product_price = intervention.total_cost
            product = intervention.env['product.template'].search(
                [['name', '=', product_name]])
            intervention.product_template_id = product if product else \
                intervention.env['product.template'].create(
                    {'name': product_name,
                     'type': 'service',
                     'list_price': product_price,
                     'intervention_id': None
                     })

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def show_expenses(self):
        return {
            'name': _('Expenses'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.move.line',
            'context': self.env.context,
            'domain': [('product_id.product_tmpl_id', '=',
                        self.product_template_id.id),
                       ('debit', '>', 0),
                       ('account_id', '=',
                        self.product_template_id.property_account_expense_id
                        .id)
                       ]
        }

    @api.multi
    def show_income(self):
        return {
            'name': _('Income'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.move.line',
            'context': self.env.context,
            'domain': [('product_id.product_tmpl_id', '=',
                        self.product_template_id.id),
                       ('credit', '>', 0),
                       ('account_id', '=',
                        self.product_template_id.property_account_income_id.id)
                       ],
        }

    @api.multi
    def show_contract(self):
        return {
            'name': _('Contract'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'recurring.contract.line',
            'context': self.env.context,
            'domain': [('product_id.product_tmpl_id', '=',
                        self.product_template_id.id)]
        }

    @api.multi
    def show_partner(self):
        contracts = self.env['recurring.contract'].search(
            [('type', 'not in', ['S', 'SC']),
             ('contract_line_ids.product_id.product_tmpl_id', '=',
              self.product_template_id.id)])

        move_lines = self.env['account.move.line'].search(
            [('product_id.product_tmpl_id', '=', self.product_template_id.id),
             ('credit', '>', 0)])

        return {
            'name': _('Partner'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'res.partner',
            'context': self.env.context,
            'domain': ['|', ('id', 'in', contracts.mapped('partner_id.id')),
                       ('id', 'in', move_lines.mapped('partner_id.id'))]
        }

    @api.multi
    def get_infos(self):
        """ Get the most recent information about the intervention """
        for intervention in self:
            if intervention.state == 'cancel':
                continue
            action_id = intervention.env.ref(
                'intervention_compassion.intervention_details_request').id

            message_vals = {
                'action_id': action_id,
                'object_id': intervention.id,
            }
            message = intervention.env['gmc.message'].with_context(
                hold_update=False).create(message_vals)
            if message.state == 'failure':
                raise UserError(message.failure_reason)
        return True

    @api.multi
    def cancel_hold(self):
        action_id = self.env.ref(
            'intervention_compassion.intervention_cancel_hold_action').id
        message = self.env['gmc.message'].with_context(
            async_mode=False).create({
                'action_id': action_id,
                'object_id': self.id
            })
        if message.state == 'failure':
            raise UserError(message.failure_reason)
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

    def intervention_hold_removal_notification(self, commkit_data):
        """
        This function is automatically executed when a
        InterventionHoldRemovalNotification Message is received. It will
        convert the message from json to odoo format and then update the
        concerned records
        :param commkit_data contains the data of the message (json)
        :return list of intervention ids which are concerned by the message
        """
        intervention_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'intervention_mapping')

        # Apparently this message contains a single dictionary, and not a
        # list of dictionaries,
        ihrn = commkit_data['InterventionHoldRemovalNotification']
        # Remove problematic type as it is not needed and contains
        # erroneous data
        del ihrn['InterventionType_Name']

        vals = intervention_mapping.get_vals_from_connect(ihrn)
        intervention_id = vals['intervention_id']

        intervention = self.env['compassion.intervention'].search([
            ('intervention_id', '=', intervention_id),
            ('hold_id', '=', vals['hold_id'])
        ])
        if intervention:
            intervention.with_context(hold_update=False).write(vals)
            intervention.hold_cancelled()

        return [intervention.id]

    @api.model
    def intervention_reporting_milestone(self, commkit_data):
        """This function is automatically executed when a
                InterventionReportingMilestoneRequestList is received,
                it send a message to the follower of the Intervention
                :param commkit_data contains the data of the
                message (json)
                :return list of intervention ids which are concerned by the
                message """
        intervention_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'intervention_mapping')
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        milestones_data = commkit_data[
            'InterventionReportingMilestoneRequestList']
        intervention_local_ids = []

        for milestone in milestones_data:
            intervention_vals = intervention_mapping.get_vals_from_connect(
                milestone)
            milestone_id = milestone.get('InterventionReportingMilestone_ID')
            intervention_id = intervention_vals.get('intervention_id')
            intervention = self.search([
                ('intervention_id', '=', intervention_id)
            ])
            if intervention:
                intervention_local_ids.append(intervention.id)
                body = "A new milestone is available"
                if milestone_id:
                    milestone_url = INTERVENTION_PORTAL_URL + milestone_id
                    body += f' at <a href="{milestone_url}" target="_blank">{milestone_url}</a>.'
                intervention.message_post(
                    body,
                    subject=(_(intervention.name + ': New milestone '
                                                   'received.')),
                    message_type='email',
                    subtype='mail.mt_comment'
                )
        return intervention_local_ids

    @api.model
    def intervention_amendement_commitment(self, commkit_data):
        """This function is automatically executed when a
        InterventionAmendmentCommitmentNotification is received,
        it send a message to the follower of the Intervention,
        and update it
        :param commkit_data contains the data of the
               message (json)
        :return list of intervention ids which are concerned
                by the message """
        # sleep to prevent a concurence error
        time.sleep(60)
        intervention_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'intervention_mapping')
        # actually commkit_data is a dictionary with a single entry which
        # value is a list of dictionary (for each record)
        interventionamendment = commkit_data[
            'InterventionAmendmentCommitmentNotification']
        intervention_local_ids = []

        v = intervention_mapping.get_vals_from_connect(interventionamendment)
        intervention_id = v['intervention_id']
        amendment_amount = interventionamendment[
            'AdditionalAmountRequestedUSD']
        intervention = self.env['compassion.intervention'].search([
            ('intervention_id', '=', intervention_id)
        ])

        if intervention:
            intervention.total_amendment += amendment_amount
            intervention.get_infos()
            intervention_local_ids.append(intervention.id)
            body = _("This intervention has been modified by amendment.")
            body += f"<br/><ul><li>Amendment ID: " \
                    f"{interventionamendment['InterventionAmendment_ID']}</li>"
            body += f"<li>Amendment Amount: {amendment_amount}</li>"
            body += f"<li>Hold ID: {interventionamendment['HoldID']}</li></ul>"
            intervention.message_post(
                body,
                subject=_(intervention.name + ": Amendment received"),
                message_type='email', subtype='mail.mt_comment')

        return intervention_local_ids

    @api.model
    def json_to_data(self, json, mapping_name=None):
        if 'ICP' in json:
            json['ICP'] = json['ICP'].split("; ")
        return super().json_to_data(json, mapping_name)


class InterventionDeliverable(models.Model):
    _name = 'compassion.intervention.deliverable'
    _inherit = 'connect.multipicklist'

    res_model = 'compassion.intervention'
    res_field = 'deliverable_level_2_ids'
