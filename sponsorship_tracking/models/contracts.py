# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, exceptions, _

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    sds_state = fields.Selection(
        '_get_sds_states', 'SDS Status', track_visibility='onchange',
        index=True, copy=False, readonly=True, default='draft')
    sds_state_date = fields.Date(
        'SDS state date', readonly=True, copy=False)
    cancel_gifts_on_termination = fields.Boolean(
        'Cancel pending gifts if sponsorship is terminated')
    color = fields.Integer('Color Index', default=0)
    no_sub_reason = fields.Char('No sub reason')
    sds_uid = fields.Many2one(
        'res.users', 'SDS Follower', default=lambda self: self.env.user,
        copy=False)
    sub_notes = fields.Text('Notes for SUB Sponsorship')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_sds_states(self):
        return [
            ('draft', _('Draft')),
            ('active', _('Active')),
            ('sub_waiting', _('Sub waiting')),
            ('sub', _('Sub')),
            ('sub_accept', _('Sub Accept')),
            ('sub_reject', _('Sub Reject')),
            ('no_sub', _('No sub')),
            ('cancelled', _('Cancelled'))
        ]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Push parent contract in SUB state. """
        contract = super(RecurringContract, self).create(vals)
        contract.parent_id._trigger_sub()
        return contract

    @api.multi
    def write(self, vals):
        if 'sds_state' in vals:
            vals['sds_state_date'] = fields.Datetime.now()
        if 'parent_id' in vals:
            self._parent_id_changed(vals['parent_id'])

        return super(RecurringContract, self).write(vals)

    @api.multi
    def unlink(self):
        """ Put parent in SUB Reject. """
        is_sub = self.filtered(lambda s: s.parent_id.sds_state == 'sub')
        is_sub.mapped('parent_id').action_sub_reject()
        # Unlink is already called in action_sub_reject
        return super(RecurringContract, self - is_sub).unlink()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """ Find parent sponsorship if any is sub_waiting. """
        super(RecurringContract, self).on_change_partner_id()

        if 'S' in self.type:
            origin_id = self.env['recurring.contract.origin'].search(
                [('type', '=', 'sub')], limit=1).id
            correspondent_id = self.correspondent_id.id
            parent_id = self._define_parent_id(correspondent_id)

            if parent_id and self.state == 'draft':
                self.parent_id = parent_id
                self.origin_id = origin_id

    @api.onchange('child_id')
    def onchange_child_id(self):
        """ Put back in SUB state if needed. """
        res = super(RecurringContract, self).onchange_child_id()
        self.parent_id._trigger_sub()
        return res

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
    def action_no_sub(self):
        return self.with_context(default_state='no_sub').sub_wizard()

    @api.multi
    def action_sub(self):
        return self.with_context(default_state='sub').sub_wizard()

    @api.multi
    def action_sub_reject(self):
        for contract in self:
            contract.partner_id.message_post(
                subject=_('{} - SUB Reject'.format(contract.child_code)),
                body=_("The sponsor doesn't want a new child.")
            )
            sub = contract.sub_sponsorship_id
            if sub and sub.state == 'draft':
                super(RecurringContract, sub).unlink()
            elif sub:
                sub.end_reason = '10'   # Subreject reason
                self.env['end.contract.wizard'].create({
                    'contract_id': sub.id
                }).end_contract()
        return self.write({
            'sds_state': 'sub_reject'
        })

    def sub_wizard(self):
        sub_model = 'sds.subsponsorship.wizard'
        wizard_id = self.env[sub_model].create({}).id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': sub_model,
            'target': 'new',
            'res_id': wizard_id,
        }

    # KANBAN GROUP METHODS
    ######################
    @api.model
    def _read_group_fill_results(
            self, domain, groupby, remaining_groupbys, aggregated_fields,
            count_field, read_group_result, read_group_order=None):
        """
        The method seems to support grouping using m2o fields only,
        while we want to group by a simple status field.
        Hence the code below - it replaces simple status values
        with (value, name) tuples.
        """
        if groupby == 'sds_state':
            state_dict = dict(self._get_sds_states())
            state_order = [s[0] for s in self._get_sds_states()
                           if 'sub' in s[0] or s[0] == 'active']
            filter_group_result = list(state_order)
            state_order = {s: state_order.index(s) for s in state_order}
            for result in read_group_result:
                state = result[groupby]
                # Only display SUB Sponsorship states
                if 'sub' in state or state == 'active':
                    result[groupby] = (state, state_dict.get(state))
                    filter_group_result[state_order[state]] = result
                    if state == 'active':
                        result['__fold'] = True
            return [r for r in filter_group_result if isinstance(r, dict)]

        return super(RecurringContract, self)._read_group_fill_results(
            domain, groupby,
            remaining_groupbys, aggregated_fields, count_field,
            read_group_result, read_group_order
        )

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_waiting(self):
        """ Make contract SDS status in active mode. """
        self.filtered(lambda s: s.sds_state == 'draft').write({
            'sds_state': 'active',
            'sds_state_date': fields.Date.today()
        })
        return super(RecurringContract, self).contract_waiting()

    @api.multi
    def contract_cancelled(self):
        """ Change SDS Follower """
        res = super(RecurringContract, self).contract_cancelled()
        self._check_need_sub()
        return res

    @api.multi
    def contract_terminated(self):
        """ Change SDS Follower """
        res = super(RecurringContract, self).contract_terminated()
        self._check_need_sub()
        return res

    @api.multi
    def contract_active(self):
        """ Change color of parent Sponsorship. """
        res = super(RecurringContract, self).contract_active()
        for sub in self.filtered(lambda s: s.parent_id.sds_state == 'sub'):
            sub.parent_id.color_id = 5  # Green
        return res

    @api.multi
    def check_sub_state(self):
        """ Called from base_action_rule to verify subs. """
        for sponsorship in self:
            if sponsorship.sub_sponsorship_id.state == 'active':
                sponsorship.sds_state = 'sub_accept'
            else:
                sponsorship.sds_state = 'sub_reject'

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _check_need_sub(self):
        """ Called when a contract is terminated, update the sds states. """
        for contract in self.filtered('child_id'):
            lang = contract.correspondent_id.lang[:2]
            sds_user = self.env['sds.follower.settings'].get_param(
                'sub_' + lang)
            if contract.end_reason == '1':  # Child departure
                # When a departure comes for a sub sponsorship, we consider
                # the sub proposal as accepted.
                if contract.parent_id.sds_state == 'sub':
                    contract.parent_id.write({
                        'sds_state': 'sub_accept',
                        'color': 5
                    })
                vals = {
                    'sds_state': 'sub_waiting',
                    'sds_uid': sds_user,
                    'color': 3  # Yellow
                }
            else:
                if contract.parent_id.sds_state == 'sub' and \
                        contract.end_reason != '13':    # 13=Exchange of child
                    # This is as subreject
                    contract.parent_id.write({
                        'sds_state': 'sub_reject',
                        'color': 2
                    })
                elif contract.parent_id.sds_state == 'sub' and \
                        contract.end_reason == '13':    # 13=Exchange of child
                    # Remove parent to allow a new subsponsorship
                    contract.with_context(
                        allow_removing_sub=True).parent_id = False
                vals = {
                    'sds_state': 'cancelled',
                    'color': 1
                }
            # Avoid updating contracts already marked as no sub
            if contract.sds_state != 'no_sub':
                contract.write(vals)

    def _define_parent_id(self, correspondent_id):
        same_partner_contracts = self.search(
            [('correspondent_id', '=', correspondent_id),
             ('sds_state', '=', 'sub_waiting')])
        for same_partner_contract in same_partner_contracts:
            if not self.search_count([
                    ('parent_id', '=', same_partner_contract.id)]):
                return same_partner_contract.id
        return False

    def _parent_id_changed(self, parent_id):
        """ If contract parent is sub_waiting, mark the sub. """
        for contract in self:
            if 'S' in contract.type:
                if contract.parent_id and not self.env.context.get(
                        'allow_removing_sub'):
                    raise exceptions.UserError(
                        _("You cannot change the sub sponsorship."))
                parent = self.browse(parent_id)
                parent._trigger_sub()

    @api.multi
    def _trigger_sub(self):
        """ Triggers the transition to SUB state if the sponsorship is in
        valid state (either sub waiting or no sub since less than 50 days)
        """
        limit = date.today() - relativedelta(days=50)
        valid_sub = self.filtered(
            lambda s: s.sds_state == 'sub_waiting' or (
                s.sds_state in ['sub_reject', 'no_sub'] and
                fields.Date.from_string(s.end_date) >= limit)
        )
        valid_sub.write({
            'sds_state': 'sub',
            'color': 2  # Red until sub is active
        })
