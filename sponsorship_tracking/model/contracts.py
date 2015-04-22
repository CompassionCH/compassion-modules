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
            cr, uid, [('sds_state', '=', value)], context)
        self.trg_validate(cr, uid, contract_ids, 'mail_sent', context)
        return True

    def button_project_mail_sent(self, cr, uid, value, context=None):
        """Button in Kanban view calling action on all contracts of one group.
        """
        contract_ids = self.search(
            cr, uid, [('project_state', '=', value)], context)
        self.trg_validate(cr, uid, contract_ids, 'project_mail_sent', context)
        return True

    _columns = {
        'sds_state': fields.selection([
            ('draft', _('Draft')),
            ('start', _('Start')),
            ('waiting_welcome', _('Waiting welcome')),
            ('active', _('Active')),
            ('field_memo', _('Field memo')),
            ('sub_waiting', _('Sub waiting')),
            ('sub', _('Sub')),
            ('sub_accept', _('Sub Accept')),
            ('sub_reject', _('Sub Reject')),
            ('no_sub', _('No sub')),
            ('cancelled', _('Cancelled'))], _('SDS Status'),
            readonly=True, track_visibility='onchange', select=True,
            help=_('')),
        'last_sds_state_change_date': fields.date(
            _('Last SDS state change date'),
            readonly=True),
        'project_id': fields.related(
            'child_id', 'project_id',
            type='many2one', string=_('Project'),
            readonly=True
        ),
        'project_state': fields.selection([
            ('active', _('Active')),
            ('inform_suspended', _('Inform suspended')),
            ('suspended', _('Suspended')),
            ('inform_reactivation', _('Inform reactivation')),
            ('inform_extension', _('Inform extension')),
            ('waiting_attribution', _('Waiting attribution')),
            ('inform_suspended_reactivation',
             _('Inform suspended and reactivation')),
            ('inform_project_terminated', _('Inform project terminated')),
            ('phase_out', _('Phase out')),
            ('terminated', _('Terminated'))], _('Project Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_('')),
        'color': fields.integer('Color Index'),
    }

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
        for contract in self.browse(cr, uid, ids, context):
            if contract.parent_id:
                wf_service = netsvc.LocalService('workflow')
                logger.info("Contract " + str(contract.id) + " contract sub.")
                wf_service.trg_validate(
                    uid, 'recurring.contract', contract.parent_id.id,
                    'new_contract_validated', cr)
        return True

    def trg_validate(self, cr, uid, ids, transition, context=None):
        """ Workflow helper for triggering a transition on contracts. """
        wf_service = netsvc.LocalService('workflow')
        for contract_id in ids:
            logger.info("{0} on Contract {1}".format(
                transition, str(contract_id)))
            wf_service.trg_validate(uid, self._name, contract_id, transition,
                                    cr)
        return True

    def check_sub_waiting_duration(self, cr, uid, context=None):
        contract_ids = self.search(
            cr, uid, [('sds_state', '=', 'sub_waiting')], context=context)

        for contract in self.browse(cr, uid, contract_ids, context):
            if contract.end_date:
                end_date = datetime.strptime(
                    contract.end_date, DF).date()
                if end_date + timedelta(days=15) < date.today():
                    wf_service = netsvc.LocalService('workflow')
                    logger.info(
                        "Contract " + str(
                            contract.id) + " sub waiting time expired")
                    wf_service.trg_validate(
                        uid, 'recurring.contract',
                        contract.id, 'no_sub', cr)
        return True

    def check_sub_duration(self, cr, uid, context=None):
        contract_ids = self.search(
            cr, uid, [('sds_state', '=', 'sub')], context=context)

        for contract in self.browse(cr, uid, contract_ids, context):
            sub_parent_contracts_ids = self.search(
                cr, uid,
                [('parent_id', '=', contract.id)],
                context=context)

            if sub_parent_contracts_ids:
                sub_parent_contracts = self.browse(
                    cr, uid, sub_parent_contracts_ids, context)
                for sub_parent_contract in sub_parent_contracts:
                    if (sub_parent_contract.state == 'active' or
                            sub_parent_contract.end_reason == 1):
                        wf_service = netsvc.LocalService('workflow')
                        wf_service = netsvc.LocalService('workflow')
                        logger.info(
                            "Contract " + str(
                                contract.id) + " sub waiting time expired")
                        wf_service.trg_validate(
                            uid, 'recurring.contract',
                            contract.id,
                            'sub_accept', cr)
                        break
                else:
                    wf_service = netsvc.LocalService('workflow')
                    wf_service = netsvc.LocalService('workflow')
                    logger.info(
                        "Contract " + str(
                            contract.id) + " sub waiting time expired")
                    wf_service.trg_validate(
                        uid, 'recurring.contract',
                        contract.id,
                        'sub_reject', cr)
        return True

    def contract_cancelled(self, cr, uid, ids, context=None):
        res = super(recurring_contract, self).contract_cancelled(
            cr, uid, ids, context)
        self.write(cr, uid, ids, {'project_state': False}, context)
        return res

    def contract_terminated(self, cr, uid, ids, context=None):
        res = super(recurring_contract, self).contract_terminated(
            cr, uid, ids, context)
        self.write(cr, uid, ids, {'project_state': False}, context)
        return res

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = super(recurring_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, context)
        origin_ids = self.pool.get('recurring.contract.origin').search(
            cr, uid,
            [('name', '=', 'SUB Sponsorship')],
            context=context)
        parent_id = self.define_parent_id(cr, uid, partner_id, context)
        origin_id = origin_ids[0] if parent_id else False

        res['value'].update({
            'parent_id': parent_id,
            'origin_id': origin_id
        })
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if 'sds_state' in vals:
            vals['last_sds_state_change_date'] = date.today()
        return super(recurring_contract, self).write(
            cr, uid, ids, vals, context)

    def define_parent_id(self, cr, uid, partner_id, context=None):
        same_partner_contracts_ids = self.search(
            cr, uid,
            [('partner_id', '=', partner_id),
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
            'res_model': 'recurring.contract',
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
