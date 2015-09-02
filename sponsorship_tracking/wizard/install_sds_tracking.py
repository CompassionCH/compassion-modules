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
from openerp import api, models
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import timedelta, datetime

SDS_COLORS = {
    'sub_accept': '5',
    'sub_reject': '2',
    'no_sub': '1',
    'sub': '0',
    'sub_waiting': '3',
    'cancelled': '1',
    'draft': '7',
    'active': '0',
}


class recurring_contract(models.TransientModel):
    _name = "install.sds.tracking"

    # Only at module installation
    @api.model
    def insert_wkf_items_for_sds_state(self):
        contract_obj = self.env['recurring.contract']
        active_contract_ids = contract_obj.search(
            [('sds_state', '=', 'active')]).ids
        draft_contract_ids = contract_obj.search(
            [('sds_state', '=', 'draft')]).ids
        project_active_contracts_ids = contract_obj.search(
            [('project_state', '=', 'active')]).ids
        project_suspended_contracts_ids = contract_obj.search(
            [('project_state', '=', 'fund-suspended')]).ids
        sub_waiting_contract_ids = contract_obj.search(
            [('sds_state', '=', 'sub_waiting')]).ids
        sub_contract_ids = contract_obj.search(
            [('sds_state', '=', 'sub')]).ids
        self.env.cr.execute(
            "SELECT id FROM wkf WHERE name = 'recurring.contract.wkf'")
        wkf_id = self.env.cr.fetchall()[0][0]

        self._ins_wkf_items('act_draft', wkf_id, draft_contract_ids)
        self._ins_wkf_items('act_active', wkf_id, active_contract_ids)
        self._ins_wkf_items(
            'act_sub_waiting', wkf_id, sub_waiting_contract_ids)
        self._ins_wkf_items('act_sub', wkf_id, sub_contract_ids)
        self._ins_wkf_items(
            'act_project_active', wkf_id, project_active_contracts_ids)
        self._ins_wkf_items(
            'act_project_suspended', wkf_id, project_suspended_contracts_ids)

    def _ins_wkf_items(self, act_id, wkf_id, cont_ids):
        if cont_ids:
            cr = self.env.cr
            ir_model_data = self.env['ir.model.data']
            wkf_activity_id = ir_model_data.get_object_reference(
                'sponsorship_tracking', act_id)[1]

            wkf_instance_ids = list()
            con_ids_string = ','.join([str(c) for c in cont_ids])
            cr.execute(
                "UPDATE wkf_instance SET state='active' "
                "WHERE wfk_id = {0} and res_id in ({1})".format(
                    wkf_id, con_ids_string))
            cr.execute(
                "SELECT id FROM wkf_instance "
                "WHERE wkf_id = {0} AND res_id in ({1})".format(
                    wkf_id, con_ids_string))
            res = cr.fetchall()
            if res:
                for row in res:
                    wkf_instance_ids.append(row[0])

            for wkf_instance_id in wkf_instance_ids:
                cr.execute(
                    "INSERT INTO wkf_workitem(act_id, inst_id, state) "
                    "VALUES ('{0}', '{1}', 'complete')".format(
                        wkf_activity_id, wkf_instance_id))

    # Only at module installation
    @api.model
    def set_sds_states(self):
        """ Rules for setting the SDS State of a contract.
            1. Draft contracts -> draft
            2. Waiting contracts -> active
            3. Active contracts -> active
            4. Cancelled contracts -> cancelled
            5. Contracts terminated by sponsor -> cancelled
            6. Contracts child departed -> no_sub, sub_accept or sub_reject
               See Method _get_contract_sub for more details.
        """
        contract_obj = self.env['recurring.contract']
        waiting_contract_ids = contract_obj.search(
            [('state', 'in', ['waiting', 'mandate'])]).ids
        active_contract_ids = contract_obj.search(
            [('state', '=', 'active')]).ids
        draft_contract_ids = contract_obj.search(
            [('state', '=', 'draft')]).ids
        cancelled_contract_ids = contract_obj.search(
            [('state', '=', 'cancelled')]).ids
        terminated_contract_ids = contract_obj.search(
            [('state', '=', 'terminated'), ('end_reason', '!=', '1')]).ids
        no_sub_ids, sub_ids, sub_accept_ids, sub_reject_ids, \
            sub_waiting_ids = self._get_contract_sub()

        self._set_sds_state(draft_contract_ids, 'draft', 'start_date')
        self._set_sds_state(waiting_contract_ids, 'active', 'start_date')
        self._set_sds_state(active_contract_ids, 'active', 'activation_date')
        self._set_sds_state(cancelled_contract_ids, 'cancelled', 'end_date')
        self._set_sds_state(terminated_contract_ids, 'cancelled', 'end_date')
        self._set_sds_state(no_sub_ids, 'no_sub', 'end_date')
        self._set_sds_state(sub_ids, 'sub', 'end_date')
        self._set_sds_state(sub_waiting_ids, 'sub_waiting', 'end_date')
        self._set_sds_state(sub_accept_ids, 'sub_accept', 'end_date', 50)
        self._set_sds_state(sub_reject_ids, 'sub_reject', 'end_date', 50)

    def _set_sds_state(self, contract_ids, sds_state, sds_change_date,
                       date_delta=0):
        if contract_ids:
            con_ids = ','.join([str(c) for c in contract_ids])
            self.env.cr.execute(
                "UPDATE recurring_contract "
                "SET sds_state = '{0}', sds_state_date = {1}+{2},"
                "    color = {3} "
                "WHERE id in ({4}) ".format(
                    sds_state, sds_change_date,
                    date_delta, SDS_COLORS[sds_state], con_ids))

    def _get_contract_sub(self):
        """ Rules for setting SUB Status of a contract with child departed:
            1. No active or cancelled/terminated SUB contract exists -> no_sub
            2. One active SUB contract exists -> sub_accept
            3. One cancelled/terminated contract exists and end_date > 50 days
               after child departure or end_reason is also a child departure
               -> sub_accept
            4. If no other condition above is met -> sub_reject
        """
        contract_obj = self.env['recurring.contract']
        max_sub_waiting = datetime.today() + timedelta(days=-50)
        child_departed_contracts = contract_obj.search(
            [('state', '=', 'terminated'), ('end_reason', '=', '1')])

        no_sub_ids = list()
        sub_ids = list()
        sub_waiting_ids = list()
        sub_accept_ids = list()
        sub_reject_ids = list()

        for contract in child_departed_contracts:
            sub_contracts = contract_obj.search(
                [('parent_id', '=', contract.id)])
            contract_end_date = datetime.strptime(contract.end_date, DF)

            if not sub_contracts:
                if contract_end_date < max_sub_waiting:
                    no_sub_ids.append(contract.id)
                else:
                    sub_waiting_ids.append(contract.id)
            else:
                for sub_contract in sub_contracts:
                    if (sub_contract.state == 'active'):
                        sub_accept_ids.append(contract.id)
                        break
                    elif sub_contract.end_date:
                        sub_end_date = datetime.strptime(
                            sub_contract.end_date, DF)
                        sub_start_date = datetime.strptime(
                            sub_contract.start_date, DF)
                        if (sub_contract.end_reason == '1' or
                            sub_end_date >
                                sub_start_date + timedelta(days=50)):
                            sub_accept_ids.append(
                                contract.id)
                            break
                    else:
                        sub_ids.append(contract.id)
                        break
                else:
                    sub_reject_ids.append(contract.id)

        return no_sub_ids, sub_ids, sub_accept_ids, sub_reject_ids, \
            sub_waiting_ids

    # Only at module installation
    @api.model
    def set_project_state(self):
        """ Pushes the state of the project to the active contracts. """
        project_obj = self.env['compassion.project']
        contract_obj = self.env['recurring.contract']
        suspended_project_ids = project_obj.search(
            [('suspension', '=', 'fund-suspended')]).ids
        suspended_project_contract_ids = contract_obj.search([
            ('project_id', 'in', suspended_project_ids),
            ('state', 'not in', ['terminated', 'cancelled'])]).ids

        active_project_ids = project_obj.search([
            ('status', '=', 'A'),
            ('id', 'not in', suspended_project_ids)]).ids
        active_project_contract_ids = contract_obj.search(
            [('project_id', 'in', active_project_ids),
             ('state', 'not in', ['terminated', 'cancelled'])]).ids

        cr = self.env.cr
        if suspended_project_contract_ids:
            cr.execute(
                "UPDATE recurring_contract "
                "SET project_state = 'fund-suspended' "
                "WHERE id IN ({0})".format(','.join(
                    [str(id) for id in suspended_project_contract_ids])))

        if active_project_contract_ids:
            cr.execute(
                "UPDATE recurring_contract "
                "SET project_state = 'active' "
                "WHERE id IN ({0})".format(','.join(
                    [str(id) for id in active_project_contract_ids])))
