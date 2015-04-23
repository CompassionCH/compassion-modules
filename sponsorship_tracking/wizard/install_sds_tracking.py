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
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import timedelta, datetime


class recurring_contract(orm.TransientModel):
    _name = "install.sds.tracking"

    # Only at module installation
    def _insert_wkf_items_for_sds_state(self, cr, uid, ids=None, context=None):
        contract_obj = self.pool.get('recurring.contract')
        active_contract_ids = contract_obj.search(
            cr, uid,
            [('sds_state', '=', 'active')],
            context)
        draft_contract_ids = contract_obj.search(
            cr, uid,
            [('sds_state', '=', 'draft')],
            context)
        project_active_contracts_ids = contract_obj.search(
            cr, uid,
            [('project_state', '=', 'active')],
            context)
        project_suspended_contracts_ids = contract_obj.search(
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
                "SELECT id FROM wkf_instance "
                "WHERE wkf_id = {0} AND res_id = {1}".format(
                    wkf_id, contract_id))
            res = cr.fetchall()
            if res:
                wkf_instance_ids.append(res[0][0])

        for wkf_instance_id in wkf_instance_ids:
            cr.execute(
                "INSERT INTO wkf_workitem(act_id, inst_id, state) "
                "VALUES ('{0}', '{1}', '{2}')".format(
                    wkf_activity_id, wkf_instance_id, 'complete'))

    # Only at module installation
    def _set_sds_states(self, cr, uid, ids=None, context=None):
        """ Rules for setting the SDS State of a contract.
            1. Draft contracts -> draft
            2. Waiting contracts -> active
            3. Active contracts -> active
            4. Cancelled contracts -> cancelled
            5. Contracts terminated by sponsor -> cancelled
            6. Contracts child departed -> no_sub, sub_accept or sub_reject
               See Method _get_contract_sub for more details.
        """
        contract_obj = self.pool.get('recurring.contract')
        waiting_contract_ids = contract_obj.search(
            cr, uid,
            [('state', 'in', ['waiting', 'mandate'])],
            context)
        active_contract_ids = contract_obj.search(
            cr, uid,
            [('state', '=', 'active')],
            context)
        draft_contract_ids = contract_obj.search(
            cr, uid,
            [('state', '=', 'draft')],
            context)
        cancelled_contract_ids = contract_obj.search(
            cr, uid,
            [('state', '=', 'cancelled')],
            context)
        terminated_contract_ids = contract_obj.search(
            cr, uid,
            [('state', '=', 'terminated'), ('end_reason', '!=', '1')],
            context)
        no_sub_ids, sub_accept_ids, sub_reject_ids = self._get_contract_sub(
            cr, uid)

        self._set_sds_state(cr, uid, draft_contract_ids, 'draft', 'start_date')
        self._set_sds_state(
            cr, uid, waiting_contract_ids, 'active', 'start_date')
        self._set_sds_state(
            cr, uid, active_contract_ids, 'active', 'activation_date')
        self._set_sds_state(
            cr, uid, cancelled_contract_ids, 'cancelled', 'end_date')
        self._set_sds_state(
            cr, uid, terminated_contract_ids, 'cancelled', 'end_date')
        self._set_sds_state(cr, uid, no_sub_ids, 'no_sub', 'end_date')
        self._set_sds_state(
            cr, uid, sub_accept_ids, 'sub_accept', 'end_date', 40)
        self._set_sds_state(
            cr, uid, sub_reject_ids, 'sub_reject', 'end_date', 40)

    def _set_sds_state(
            self, cr, uid, contract_ids, sds_state,
            sds_change_date, date_delta=0):
        for contract_id in contract_ids:
            cr.execute(
                "UPDATE recurring_contract "
                "SET sds_state = '{0}', last_sds_state_change_date = {1}+{2} "
                "WHERE id = '{3}' ".format(
                    sds_state, sds_change_date,
                    date_delta, contract_id))

    # Only at module installation
    def _get_contract_sub(self, cr, uid, ids=None, context=None):
        """ Rules for setting SUB Status of a contract with child departed:
            1. No active or cancelled/terminated SUB contract exists -> no_sub
            2. One active SUB contract exists -> sub_accept
            3. One cancelled/terminated contract exists and end_date > 40 days
               after child departure or end_reason is also a child departure
               -> sub_accept
            4. If no other condition above is met -> sub_reject
        """
        contract_obj = self.pool.get('recurring.contract')
        child_departed_contract_ids = contract_obj.search(
            cr, uid,
            [('state', '=', 'terminated'), ('end_reason', '=', '1')],
            context=context)

        no_sub_ids = list()
        sub_accept_ids = list()
        sub_reject_ids = list()

        for child_departed_contract_id in child_departed_contract_ids:
            contract = contract_obj.browse(
                cr, uid, child_departed_contract_id, context)

            sub_contract_ids = contract_obj.search(
                cr, uid,
                [('parent_id', '=', child_departed_contract_id),
                 ('state', 'in', ['active', 'terminated', 'cancelled'])],
                context)
            if not (sub_contract_ids):
                no_sub_ids.append(child_departed_contract_id)
            else:
                for sub_contract_id in sub_contract_ids:
                    sub_contract = contract_obj.browse(
                        cr, uid, sub_contract_id, context)
                    if (sub_contract.state == 'active'):
                        sub_accept_ids.append(
                            child_departed_contract_id)
                        break
                    else:
                        if sub_contract.end_date and contract.end_date:
                            parent_end_date = datetime.strptime(
                                sub_contract.end_date, DF)
                            contract_end_date = datetime.strptime(
                                contract.end_date, DF)
                            if (sub_contract.end_reason == '1' or
                                parent_end_date >
                                    contract_end_date + timedelta(days=40)):
                                sub_accept_ids.append(
                                    child_departed_contract_id)
                                break
                else:
                    sub_reject_ids.append(child_departed_contract_id)

        return no_sub_ids, sub_accept_ids, sub_reject_ids

    def _set_project_state(self, cr, uid, ids=None, context=None):
        """ Pushes the state of the project to the active contracts. """
        compassion_project_obj = self.pool.get('compassion.project')
        contract_obj = self.pool.get('recurring.contract')
        suspended_project_ids = compassion_project_obj.search(
            cr, uid, [('suspension', '=', 'fund-suspended')], context=context)
        suspended_project_contract_ids = contract_obj.search(cr, uid, [
            ('project_id', 'in', suspended_project_ids),
            ('state', 'not in', ['terminated', 'cancelled'])
            ], context=context)

        active_project_ids = compassion_project_obj.search(cr, uid, [
            ('status', '=', 'A'),
            ('id', 'not in', suspended_project_ids)], context=context)
        active_project_contract_ids = contract_obj.search(
            cr, uid,
            [('project_id', 'in', active_project_ids),
             ('state', 'not in', ['terminated', 'cancelled'])],
            context)

        cr.execute(
            "UPDATE recurring_contract "
            "SET project_state = 'suspended' "
            "WHERE id IN ({0})".format(','.join(
                [str(id) for id in suspended_project_contract_ids])))

        cr.execute(
            "UPDATE recurring_contract "
            "SET project_state = 'active' "
            "WHERE id IN ({0})".format(','.join(
                [str(id) for id in active_project_contract_ids])))
