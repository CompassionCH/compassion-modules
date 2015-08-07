# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, fields, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime, date, timedelta
import logging
import pdb


logger = logging.getLogger(__name__)


class recurring_contract(models.Model):
    _inherit = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    sds_state = fields.Selection(
        '_get_sds_states', 'SDS Status', readonly=True,
        track_visibility='onchange', select=True, copy=False)
    sds_state_date = fields.Date(
        'SDS state date', readonly=True, copy=False)
    project_id = fields.Many2one(
        'compassion.project', 'Project', related='child_id.project_id',
        readonly=True)
    project_state = fields.Selection(
        '_get_project_states', 'Project Status', select=True,
        readonly=True, track_visibility='onchange')
    color = fields.Integer('Color Index')
    no_sub_reason = fields.Char('No sub reason')
    sds_uid = fields.Many2one(
        'res.users', 'SDS Follower', default=lambda self: self.env.user)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_sds_states(self):
        return [
            ('draft', _('Draft')),
            ('start', _('Start')),
            ('waiting_welcome', _('Waiting welcome')),
            ('active', _('Active')),
            ('field_memo', _('Field memo')),
            ('sub_waiting', _('Sub waiting')),
            ('sub', _('Sub')),
            ('sub_accept', _('Sub Accept')),
            ('sub_reject', _('Sub Reject')),
            ('inform_no_sub', _('Inform No sub')),
            ('no_sub', _('No sub')),
            ('cancelled', _('Cancelled'))
        ]

    def _get_project_states(self):
        return [
            ('active', _('Active')),
            ('inform_suspended', _('Inform fund suspension')),
            ('fund-suspended', _('Fund Suspended')),
            ('inform_reactivation', _('Inform reactivation')),
            ('inform_extension', _('Inform extension')),
            ('inform_suspended_reactivation',
             _('Inform suspended and reactivation')),
            ('inform_project_terminated', _('Inform project terminated')),
            ('phase_out', _('Phase out')),
            ('terminated', _('Terminated'))
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        if 'sds_state' in vals:
            vals['sds_state_date'] = date.today().strftime(DF)
        if 'parent_id' in vals:
            self._parent_id_changed(vals['parent_id'])

        return super(recurring_contract, self).write(vals)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################

    # Kanban Buttons
    ################
    @api.model
    def button_mail_sent(self, value):
        """Button in Kanban view calling action on all contracts of one group.
        """
        contracts = self.search([('sds_state', '=', value)])
        contracts.signal_workflow('mail_sent')
        return True

    @api.model
    def button_project_mail_sent(self, value):
        """Button in Kanban view calling action on all contracts of one group.
        """
        contracts = self.search([('project_state', '=', value)])
        contracts.signal_workflow('project_mail_sent')
        return True

    @api.model
    def button_reset_gmc_state(self, value):
        """ Button called from Kanban view on all contracts of one group. """
        contracts = self.search([('gmc_state', '=', value)])
        return contracts.reset_gmc_state()

    # CRON Methods
    ##############
    @api.model
    def check_sub_duration(self):
        """ Check all sponsorships in SUB State.
            After 50 days SUB Sponsorship started, Sponsorship becomes :
                - SUB Accept if SUB sponsorship is active
                - SUB Reject otherwise
        """
        fifty_days_ago = date.today() + timedelta(days=-50)
        contracts = self.search([('sds_state', '=', 'sub')])

        for contract in contracts:
            transition = 'sub_reject'
            sub_sponsorships = self.search([('parent_id', '=', contract.id)])
            if sub_sponsorships:
                for sub_contract in sub_sponsorships:
                    if sub_contract.state == 'active' or \
                            sub_contract.end_reason == 1:
                        transition = 'sub_accept'
                        break

                contract.write({'color': 5 if transition == 'sub_accept'
                                else 2})
                sub_start_date = datetime.strptime(
                    sub_contract.start_date, DF).date()
                if sub_start_date < fifty_days_ago:
                    contract.signal_workflow(transition)

        return True

    @api.model
    def check_waiting_welcome_duration(self):
        """ Check all sponsorships in Waiting Welcome state. Put them in
            light green color after 10 days, indicating the mailing should
            be sent.
        """
        ten_days_ago = date.today() + timedelta(days=-10)
        contracts = self.search([
            ('sds_state_date', '<', ten_days_ago),
            ('sds_state', '=', 'waiting_welcome')])
        return contracts.write({'color': 4})

    @api.model
    def end_workflow(self):
        """ Terminate all workflows related to inactive contracts. """
        inactive_contracts = self.search([
            ('sds_state', 'in', ['cancelled', 'no_sub', 'sub_accept',
                                 'sub_reject']),
            ('state', 'in', ['terminated', 'cancelled'])])
        inactive_contracts.delete_workflow()
        return True

    # Other view callbacks
    ######################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """ Find parent sponsorship if any is sub_waiting. """
        super(recurring_contract, self).on_change_partner_id()

        if 'S' in self.type:
            origin_id = self.env['recurring.contract.origin'].search(
                [('type', '=', 'sub')]).ids[0]
            correspondant_id = self.correspondant_id.id
            parent_id = self._define_parent_id(correspondant_id)

            if parent_id and self.state == 'draft':
                self.parent_id = parent_id
                self.origin_id = origin_id

    @api.multi
    def switch_contract_view(self):
        ir_model_data = self.env['ir.model.data']
        view_id = ir_model_data.get_object_reference(
            'sponsorship_tracking',
            self.env.context['view_id'])[1]

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'target': 'current',
            "res_id": self.ids[0],
        }

    @api.multi
    def mail_sent(self):
        return self.signal_workflow('mail_sent')

    @api.multi
    def project_mail_sent(self):
        return self.signal_workflow('project_mail_sent')

    # KANBAN GROUP METHODS
    ######################
    @api.model
    def sds_kanban_groups(self, ids, domain, **kwargs):
        fold = {
            'active': True,
            'sub_accept': True,
            'sub_reject': True,
            'no_sub': True,
            'cancelled': True
        }
        sds_states = self._get_sds_states()
        display_states = list()
        for sds_state in sds_states:
            sponsorship_count = self.search_count([
                ('sds_state', '=', sds_state[0])])
            if sponsorship_count:
                display_states.append(sds_state)
        return display_states, fold

    @api.model
    def _read_group_fill_results(self, domain, groupby,
                                 remaining_groupbys, aggregated_fields,
                                 count_field, read_group_result,
                                 read_group_order=None):
        """
        The method seems to support grouping using m2o fields only,
        while we want to group by a simple status field.
        Hence the code below - it replaces simple status values
        with (value, name) tuples.
        """
        if groupby == 'sds_state':
            state_dict = dict(self._get_sds_states())
            for result in read_group_result:
                state = result[groupby]
                result[groupby] = (state, state_dict.get(state))

        return super(recurring_contract, self)._read_group_fill_results(
            domain, groupby,
            remaining_groupbys, aggregated_fields, count_field,
            read_group_result, read_group_order
        )

    _group_by_full = {
        'sds_state': sds_kanban_groups,
    }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_validation(self):
        pdb.set_trace()
        for contract in self:
            if contract.parent_id:
                logger.info("Contract " + str(contract.id) + " contract sub.")
                contract.parent_id.signal_workflow('new_contract_validated')
        return True

    @api.multi
    def contract_cancelled(self):
        """ Project state is no more relevant when contract is cancelled. """
        res = super(recurring_contract, self).contract_cancelled()
        self.write({'project_state': False})
        return res

    @api.multi
    def contract_terminated(self):
        """ Project state is no more relevant when contract is terminated.
        We also put the person who terminated the contract as follower. """
        res = super(recurring_contract, self).contract_terminated()
        self.write({'project_state': False,
                    'sds_uid': self.env.user.id})
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _define_parent_id(self, correspondant_id):
        same_partner_contracts = self.search(
            [('correspondant_id', '=', correspondant_id),
             ('sds_state', '=', 'sub_waiting')])
        for same_partner_contract in same_partner_contracts:
            if not self.search_count([
                    ('parent_id', '=', same_partner_contract.id)]):
                return same_partner_contract.id
        return False

    def _parent_id_changed(self, parent_id):
        """ If contract is already validated and parent is sub_waiting,
        mark the sub. """
        for contract in self:
            if 'S' in contract.type and contract.state != 'draft':
                if contract.parent_id:
                    raise exceptions.Warning(
                        _("Operation Failure"),
                        _("You cannot change the sub sponsorship."))
                parent = self.browse(parent_id)
                if parent.sds_state == 'sub_waiting':
                    parent.signal_workflow('new_contract_validated')
