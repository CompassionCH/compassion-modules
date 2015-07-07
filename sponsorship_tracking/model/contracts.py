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
from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import datetime, date, timedelta
import logging


logger = logging.getLogger(__name__)


class recurring_contract(orm.Model):
    _inherit = "recurring.contract"

    def button_mail_sent(self, cr, uid, value, context=None):
        """Button in Kanban view calling action on all contracts of one group.
        """
        contract_ids = self.search(
            cr, uid, [('sds_state', '=', value)], context=context)
        self.trg_validate(cr, uid, contract_ids, 'mail_sent', context)
        return True

    def button_project_mail_sent(self, cr, uid, value, context=None):
        """Button in Kanban view calling action on all contracts of one group.
        """
        contract_ids = self.search(
            cr, uid, [('project_state', '=', value)], context=context)
        self.trg_validate(cr, uid, contract_ids, 'project_mail_sent', context)
        return True

    def button_reset_gmc_state(self, cr, uid, value, context=None):
        """ Button called from Kanban view on all contracts of one group. """
        ids = self.search(cr, uid, [
            ('gmc_state', '=', value)], context=context)
        return self.reset_gmc_state(cr, uid, ids, context)

    def _get_sds_states(self, cr, uid, context=None):
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

    def _get_project_states(self, cr, uid, context=None):
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

    _columns = {
        'sds_state': fields.selection(
            _get_sds_states, _('SDS Status'), readonly=True,
            track_visibility='onchange', select=True),
        'last_sds_state_change_date': fields.date(
            _('SDS state date'),
            readonly=True),
        'project_id': fields.related(
            'child_id', 'project_id', relation='compassion.project',
            type='many2one', string=_('Project'),
            readonly=True
        ),
        'project_state': fields.selection(
            _get_project_states, _('Project Status'), select=True,
            readonly=True, track_visibility='onchange'),
        'color': fields.integer('Color Index'),
        'no_sub_reason': fields.char(_("No sub reason")),
        'sds_uid': fields.many2one('res.users', string=_("SDS Follower"))
    }

    _defaults = {
        'sds_uid': lambda self, cr, uid, c=None: uid
    }

    ##########################################################################
    #                          KANBAN GROUP METHODS                          #
    ##########################################################################
    def sds_kanban_groups(self, cr, uid, ids, domain, **kwargs):
        fold = {
            'active': True,
            'sub_accept': True,
            'sub_reject': True,
            'no_sub': True,
            'cancelled': True
        }
        sds_states = self._get_sds_states(cr, uid)
        display_states = list()
        for sds_state in sds_states:
            sponsorship_ids = self.search(cr, uid, [
                ('sds_state', '=', sds_state[0])])
            if sponsorship_ids:
                display_states.append(sds_state)
        return display_states, fold

    _group_by_full = {
        'sds_state': sds_kanban_groups,
    }

    def _read_group_fill_results(self, cr, uid, domain, groupby,
                                 remaining_groupbys, aggregated_fields,
                                 read_group_result,
                                 read_group_order=None, context=None):
        """
        The method seems to support grouping using m2o fields only,
        while we want to group by a simple status field.
        Hence the code below - it replaces simple status values
        with (value, name) tuples.
        """
        if groupby == 'sds_state':
            state_dict = dict(self._get_sds_states(cr, uid, context))
            for result in read_group_result:
                state = result[groupby]
                result[groupby] = (state, state_dict.get(state))

        return super(recurring_contract, self)._read_group_fill_results(
            cr, uid, domain, groupby, remaining_groupbys, aggregated_fields,
            read_group_result, read_group_order, context
        )

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = dict()
        default.update({
            'sds_state': 'draft',
            'last_sds_state_change_date': False,
        })
        return super(recurring_contract, self).copy(
            cr, uid, id, default, context)

    def contract_validation(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for contract in self.browse(cr, uid, ids, context):
            if contract.parent_id:
                logger.info("Contract " + str(contract.id) + " contract sub.")
                wf_service.trg_validate(
                    uid, self._name, contract.parent_id.id,
                    'new_contract_validated', cr)
        return True

    def mail_sent(self, cr, uid, contract_id, context=None):
        return self.trg_validate(cr, uid, [contract_id], 'mail_sent', context)

    def project_mail_sent(self, cr, uid, contract_id, context=None):
        return self.trg_validate(cr, uid, [contract_id], 'project_mail_sent',
                                 context)

    def trg_validate(self, cr, uid, ids, transition, context=None):
        """ Workflow helper for triggering a transition on contracts. """
        wf_service = netsvc.LocalService('workflow')
        for contract_id in ids:
            logger.info("{0} on Contract {1}".format(
                transition, str(contract_id)))
            wf_service.trg_validate(uid, self._name, contract_id, transition,
                                    cr)
        return True

    def check_sub_duration(self, cr, uid, context=None):
        """ Check all sponsorships in SUB State.
            After 50 days SUB Sponsorship started, Sponsorship becomes :
                - SUB Accept if SUB sponsorship is active
                - SUB Reject otherwise
        """
        fifty_days_ago = date.today() + timedelta(days=-50)
        contract_ids = self.search(cr, uid, [
            ('sds_state', '=', 'sub')], context=context)

        for contract in self.browse(cr, uid, contract_ids, context):
            transition = 'sub_reject'
            sub_sponsorship_ids = self.search(
                cr, uid,
                [('parent_id', '=', contract.id)],
                context=context)
            if sub_sponsorship_ids:
                for sub_contract in self.browse(cr, uid, sub_sponsorship_ids,
                                                context):
                    if sub_contract.state == 'active' or \
                            sub_contract.end_reason == 1:
                        transition = 'sub_accept'
                        break

                contract.write({'color': 5 if transition == 'sub_accept'
                                else 2})
                sub_start_date = datetime.strptime(
                    sub_contract.start_date, DF).date()
                if sub_start_date < fifty_days_ago:
                    self.trg_validate(cr, uid, [contract.id], transition,
                                      context)

        return True

    def check_waiting_welcome_duration(self, cr, uid, context=None):
        """ Check all sponsorships in Waiting Welcome state. Put them in
            light green color after 10 days, indicating the mailing should
            be sent.
        """
        ten_days_ago = date.today() + timedelta(days=-10)
        ids = self.search(cr, uid, [
            ('last_sds_state_change_date', '<', ten_days_ago),
            ('sds_state', '=', 'waiting_welcome')], context=context)
        return self.write(cr, uid, ids, {'color': 4}, context)

    def contract_cancelled(self, cr, uid, ids, context=None):
        """ Project state is no more relevant when contract is cancelled. """
        res = super(recurring_contract, self).contract_cancelled(
            cr, uid, ids, context)
        self.write(cr, uid, ids, {'project_state': False}, context)
        return res

    def contract_terminated(self, cr, uid, ids, context=None):
        """ Project state is no more relevant when contract is terminated.
        We also put the person who terminated the contract as follower. """
        res = super(recurring_contract, self).contract_terminated(
            cr, uid, ids, context)
        self.write(cr, uid, ids, {'project_state': False,
                                  'sds_uid': uid}, context)
        return res

    def on_change_partner_id(self, cr, uid, ids, partner_id,
                             type, context=None):
        """ Find parent sponsorship if any is sub_waiting. """
        res = super(recurring_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, type, context)

        if 'S' in type:
            origin_id = self.pool.get('recurring.contract.origin').search(
                cr, uid, [('type', '=', 'sub')], context=context)[0]
            correspondant_id = partner_id

            if ids:
                contract = self.browse(cr, uid, ids[0], context)
                if 'correspondant_id' in res['value']:
                    correspondant_id = res['value']['correspondant_id']
                else:
                    correspondant_id = contract.correspondant_id.id

            parent_id = self.define_parent_id(cr, uid, correspondant_id,
                                              context)

            if parent_id and (not ids or contract.state == 'draft'):
                res['value']['parent_id'] = parent_id
                res['value']['origin_id'] = origin_id

        return res

    def _parent_id_changed(self, cr, uid, ids, parent_id, context=None):
        """ If contract is already validated and parent is sub_waiting,
        mark the sub. """
        for contract in self.browse(cr, uid, ids, context):
            if 'S' in contract.type and contract.state != 'draft':
                if contract.parent_id:
                    raise orm.except_orm(
                        _("Operation Failure"),
                        _("You cannot change the sub sponsorship."))
                parent = self.browse(cr, uid, parent_id, context)
                if parent.sds_state == 'sub_waiting':
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        uid, 'recurring.contract', parent_id,
                        'new_contract_validated', cr)

    def write(self, cr, uid, ids, vals, context=None):
        if 'sds_state' in vals:
            vals['last_sds_state_change_date'] = date.today()
        if 'parent_id' in vals:
            self._parent_id_changed(cr, uid, ids, vals['parent_id'], context)

        return super(recurring_contract, self).write(
            cr, uid, ids, vals, context)

    def define_parent_id(self, cr, uid, correspondant_id, context=None):
        same_partner_contracts_ids = self.search(
            cr, uid,
            [('correspondant_id', '=', correspondant_id),
             ('sds_state', '=', 'sub_waiting')],
            context=context)
        same_partner_contracts = self.browse(
            cr, uid, same_partner_contracts_ids, context)
        if same_partner_contracts:
            for same_partner_contract in same_partner_contracts:
                if not (self.search(
                        cr, uid,
                        [('parent_id', '=', same_partner_contract.id)],
                        context=context)):
                    return same_partner_contract.id
        return False

    def switch_contract_view(self, cr, uid, contract_id, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        view_id = ir_model_data.get_object_reference(
            cr, uid, 'sponsorship_tracking',
            context['view_id'])[1]

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'target': 'current',
            "res_id": contract_id[0],
        }

    def end_workflow(self, cr, uid, context=None):
        """ Terminate all workflows related to inactive contracts. """
        wf_service = netsvc.LocalService('workflow')
        ids = self.search(cr, uid, [
            ('sds_state', 'in', ['cancelled', 'no_sub', 'sub_accept',
                                 'sub_reject']),
            ('state', 'in', ['terminated', 'cancelled'])], context=context)
        for contract_id in ids:
            wf_service.trg_delete(uid, self._name, contract_id, cr)
        return True
