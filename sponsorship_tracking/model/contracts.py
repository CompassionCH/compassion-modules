# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
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

    # Only at module installation
    def _insert_wkf_items_for_sds_state(self, cr, uid, ids=None, context=None):
        active_contract_ids = self.search(
            cr, uid,
            [('sds_state', '=', 'active')],
            context)
        draft_contract_ids = self.search(
            cr, uid,
            [('sds_state', '=', 'draft')],
            context)
        project_active_contracts_ids = self.search(
            cr, uid,
            [('project_state', '=', 'active')],
            context)
        project_suspended_contracts_ids = self.search(
            cr, uid,
            [('project_state', '=', 'suspended')],
            context)
        cr.execute(
            '''
            SELECT id FROM wkf
            WHERE name = 'recurring.contract.wkf'
            ''')
        res = cr.fetchall()
        wkf_id = res[0][0]

        self._ins_wkf_items(
            cr, uid, 'act_draft',
            wkf_id, draft_contract_ids, context)
        self._ins_wkf_items(
            cr, uid, 'act_active',
            wkf_id, active_contract_ids, context)
        self._ins_wkf_items(
            cr, uid, 'act_project_active',
            wkf_id, project_active_contracts_ids, context)
        self._ins_wkf_items(
            cr, uid, 'act_project_suspended',
            wkf_id, project_suspended_contracts_ids, context)

    def _ins_wkf_items(self, cr, uid, act_id, wkf_id, cont_ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        wkf_activity_id = ir_model_data.get_object_reference(
            cr, uid, 'sponsorship_tracking',
            act_id)[1]

        wkf_instance_ids = list()
        for contract_id in cont_ids:
            cr.execute(
                '''
                    SELECT id FROM wkf_instance
                    WHERE wkf_id = {} AND res_id = {}
                    '''.format(wkf_id, contract_id))
            res = cr.fetchall()
            if res:
                wkf_instance_ids.append(res[0][0])

        for wkf_instance_id in wkf_instance_ids:
            cr.execute(
                '''
                    INSERT INTO wkf_workitem(act_id, inst_id, state)
                    VALUES ('{}', '{}', '{}')
                    '''.format(wkf_activity_id, wkf_instance_id, 'complete')
            )

    def _get_contract_ids(prop_obj, cr, uid, ids, context=None):
        contract_ids_to_update = list()
        for project in prop_obj.browse(cr, uid, ids, context):
            contract_obj = prop_obj.pool.get('recurring.contract')
            child_obj = prop_obj.pool.get('compassion.child')
            child_ids = child_obj.search(
                cr, uid, [('code', 'like', project.code)], context=context)
            contract_ids = contract_obj.search(
                cr, uid, [('child_id', 'in', child_ids)], context=context)
            contract_ids_to_update.extend(contract_ids)
        return contract_ids_to_update

    # Only at module installation
    def _set_sds_state(self, cr, uid, ids=None, context=None):
        active_contract_ids = self.search(
            cr, uid,
            [('state', 'in', ['waiting', 'active', 'mandate'])],
            context)
        draft_contract_ids = self.search(
            cr, uid,
            [('state', '=', 'draft')],
            context)

        for active_contract_id in active_contract_ids:
            cr.execute(
                '''
                UPDATE recurring_contract
                SET sds_state = 'active'
                WHERE id = '{}'
                '''.format(active_contract_id)
            )
        for draft_contract_id in draft_contract_ids:
            cr.execute(
                '''
                UPDATE recurring_contract
                SET sds_state = 'draft'
                WHERE id = '{}'
                '''.format(draft_contract_id)
            )
    # Only at module installation

    def _set_project_state(self, cr, uid, ids=None, context=None):
        suspended_project_ids = self.pool.get('compassion.project').search(
            cr, uid, [('status', '=', 'S')], context=context)
        suspended_project_contract_ids = self.search(
            cr, uid,
            [('project_id', 'in', suspended_project_ids),
             ('state', 'not in', ['terminated', 'cancelled'])],
            context)

        active_project_ids = self.pool.get('compassion.project').search(
            cr, uid, [('status', '=', 'A')], context=context)
        active_project_contract_ids = self.search(
            cr, uid,
            [('project_id', 'in', active_project_ids),
             ('state', 'not in', ['terminated', 'cancelled'])],
            context)

        for suspended_project_contract_id in suspended_project_contract_ids:
            cr.execute(
                '''
                UPDATE recurring_contract
                SET project_state = 'suspended'
                WHERE id = '{}'
                '''.format(suspended_project_contract_id)
            )

        for active_project_contract_id in active_project_contract_ids:
            cr.execute(
                '''
                UPDATE recurring_contract
                SET project_state = 'active'
                WHERE id = '{}'
                '''.format(active_project_contract_id)
            )

    _columns = {
        'sds_state': fields.selection([
            ('draft', _('Draft')),
            ('start', _('Start')),
            ('waiting_welcome', _('Waiting welcome')),
            ('active', _('Active')),
            ('field_memo', _('Field memo')),
            ('cancelled', _('Cancelled')),
            ('sub_waiting', _('Sub waiting')),
            ('no_sub', _('No sub')),
            ('sub', _('Sub')),
            ('sub_accept', _('Accept sub')),
            ('sub_reject', _('Reject sub'))], _('SDS Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_('')),
        'date_welcome': fields.date(_('Welcome date'), readonly=True),
        'date_sub': fields.related(
            'parent_id', 'start_date',
            type='date', string=_('Date sub'),
            store=True, readonly=True),
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
            ('waiting_attribution', _('Waiting attribution')),
            ('inform_suspended_reactivation',
             _('Inform suspended and reactivation')),
            ('inform_project_terminated', _('Inform project terminated')),
            ('phase_out', _('Phase out')),
            ('terminated', _('Terminated'))], _('Project Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_('')),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = dict()
        default.update({
            'sds_state': 'draft',
            'date_welcome': False,
        })
        return super(recurring_contract, self).copy(
            cr, uid, id, default, context)

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'draft'}, context)
        return True

    def start(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'start'}, context)
        return True

    def waiting_welcome(self, cr, uid, ids, context=None):
        welcome_date = date.today() + timedelta(days=10)
        self.write(
            cr, uid, ids,
            {'sds_state': 'waiting_welcome',
             'date_welcome': welcome_date},
            context)

        return True

    def contract_validation(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            if contract.parent_id:
                wf_service = netsvc.LocalService('workflow')
                logger.info("Contract " + str(contract.id) + " contract sub.")
                wf_service.trg_validate(
                    uid, 'recurring.contract', contract.parent_id.id,
                    'new_contract_validated', cr)
        return True

    def activate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'active'}, context)

    def waiting_for_sub(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'sub_waiting'}, context)

    def sub(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'sub'}, context)

    def no_sub(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'no_sub'}, context)

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'cancelled'}, context)

    def sub_accept(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'sub_accept'}, context)

    def sub_reject(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sds_state': 'sub_reject'}, context)

    def inform_project_suspended(self, cr, uid, ids, context=None):
        self.write(
            cr, uid, ids, {'project_state': 'inform_suspended'}, context)

    def inform_project_terminated(self, cr, uid, ids, context=None):
        self.write(
            cr, uid, ids,
            {'project_state': 'inform_project_terminated'},
            context)

    def inform_project_reactivation(self, cr, uid, ids, context=None):
        self.write(
            cr, uid, ids, {'project_state': 'inform_reactivation'}, context)

    def suspended(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'suspended'}, context)

    def project_active(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'project_active'}, context)

    def project_terminated(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'terminated'}, context)

    def project_phase_out(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'phase_out'}, context)

    def welcome_sent(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " welcome sent.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'welcome_sent', cr)
        return True

    def mail_sent(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " mail sent.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'mail_sent', cr)
        return True

    def reactivate_project(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " project reactivated.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'project_reactivation', cr)

    def terminate_project(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " project terminated.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'project_terminated', cr)

    def phase_out_project(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " project phase out.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'project_phase_out', cr)

    def suspend_project(self, cr, uid, contract_id, context=None):
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " project suspended.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'project_suspended', cr)

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
            if contract.date_sub:
                date_sub = datetime.strptime(
                    contract.date_sub, DF).date()
                if date_sub + timedelta(days=15) < date.today():
                    wf_service = netsvc.LocalService('workflow')
                    logger.info(
                        "Contract " + str(
                            contract.id) + " sub waiting time expired")
                    wf_service.trg_validate(
                        uid, 'recurring.contract',
                        contract.id,
                        'sub_accept', cr)
        return True

    def contract_cancelled(self, cr, uid, ids, context=None):
        res = super(recurring_contract, self).contract_cancelled(
            cr, uid, ids, context)
        for contract in self.browse(cr, uid, ids, context):
            if contract.parent_id:
                wf_service = netsvc.LocalService('workflow')
                logger.info("Contract " + str(contract.id) + " sub rejected")
                wf_service.trg_validate(
                    uid, 'recurring.contract',
                    contract.parent_id.id,
                    'sub_reject', cr)
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
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'recurring.contract',
            'type': 'ir.actions.act_window',
            'target': 'current',
            "res_id": contract_id[0],
        }
