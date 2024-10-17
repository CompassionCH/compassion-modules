##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from psycopg2 import sql

from odoo import api, models

SDS_COLORS = {
    "sub_accept": "5",
    "sub_reject": "2",
    "no_sub": "1",
    "sub": "0",
    "sub_waiting": "3",
    "cancelled": "1",
    "draft": "7",
    "active": "0",
}


class InstallSdsTracking(models.AbstractModel):
    _name = "install.sds.tracking"
    _description = "Install SDS Tracking"

    # Use this from a shell to initialize the SDS tracking data.
    @api.model
    def set_sds_states(self):
        """Rules for setting the SDS State of a contract.
        1. Draft contracts -> draft
        2. Waiting contracts -> active
        3. Active contracts -> active
        4. Cancelled contracts -> cancelled
        5. Contracts terminated by sponsor -> cancelled
        6. Contracts child departed -> no_sub, sub_accept or sub_reject
           See Method _get_contract_sub for more details.
        """
        contract_obj = self.env["recurring.contract"]
        depart = self.env.ref("sponsorship_compassion.end_reason_depart")
        waiting_contract_ids = contract_obj.search(
            [("state", "in", ["waiting", "mandate"])]
        ).ids
        active_contract_ids = contract_obj.search([("state", "=", "active")]).ids
        draft_contract_ids = contract_obj.search([("state", "=", "draft")]).ids
        cancelled_contract_ids = contract_obj.search([("state", "=", "cancelled")]).ids
        terminated_contract_ids = contract_obj.search(
            [("state", "=", "terminated"), ("end_reason_id", "!=", depart.id)]
        ).ids
        (
            no_sub_ids,
            sub_ids,
            sub_accept_ids,
            sub_reject_ids,
            sub_waiting_ids,
        ) = self._get_contract_sub()

        self._set_sds_state(draft_contract_ids, "draft", "start_date")
        self._set_sds_state(waiting_contract_ids, "active", "start_date")
        self._set_sds_state(active_contract_ids, "active", "activation_date")
        self._set_sds_state(cancelled_contract_ids, "cancelled", "end_date")
        self._set_sds_state(terminated_contract_ids, "cancelled", "end_date")
        self._set_sds_state(no_sub_ids, "no_sub", "end_date")
        self._set_sds_state(sub_ids, "sub", "end_date")
        self._set_sds_state(sub_waiting_ids, "sub_waiting", "end_date")
        self._set_sds_state(sub_accept_ids, "sub_accept", "end_date", 50)
        self._set_sds_state(sub_reject_ids, "sub_reject", "end_date", 50)

    def _set_sds_state(self, contract_ids, sds_state, sds_change_date, date_delta=0):
        if contract_ids:
            query = sql.SQL(
                """
                    UPDATE recurring_contract
                    SET sds_state = %s,
                        sds_state_date = {column} + interval '%s days',
                        color = %s
                    WHERE id IN %s
                """
            ).format(
                column=sql.Identifier(sds_change_date)
            )  # Safely inserting a column name in the query
            query_params = (
                sds_state,
                date_delta,
                SDS_COLORS[sds_state],
                tuple(contract_ids),
            )
            self.env.cr.execute(query, query_params)

    def _get_contract_sub(self):
        """Rules for setting SUB Status of a contract with child departed:
        1. No active or cancelled/terminated SUB contract exists -> no_sub
        2. One active SUB contract exists -> sub_accept
        3. One cancelled/terminated contract exists and end_date > 50 days
           after child departure or end_reason is also a child departure
           -> sub_accept
        4. If no other condition above is met -> sub_reject
        """
        contract_obj = self.env["recurring.contract"]
        depart = self.env.ref("sponsorship_compassion.end_reason_depart")
        max_sub_waiting = datetime.today() + timedelta(days=-50)
        child_departed_contracts = contract_obj.search(
            [
                ("state", "=", "terminated"),
                ("end_reason_id", "in", [depart.id, False]),
                ("end_date", "!=", False),
            ]
        )

        no_sub_ids = list()
        sub_ids = list()
        sub_waiting_ids = list()
        sub_accept_ids = list()
        sub_reject_ids = list()

        depart = self.env.ref("sponsorship_compassion.end_reason_depart")

        for contract in child_departed_contracts:
            sub_contracts = contract_obj.search([("parent_id", "=", contract.id)])
            contract_end_date = contract.end_date

            if not sub_contracts:
                if contract_end_date < max_sub_waiting:
                    no_sub_ids.append(contract.id)
                else:
                    sub_waiting_ids.append(contract.id)
            else:
                for sub_contract in sub_contracts:
                    if sub_contract.state == "active":
                        sub_accept_ids.append(contract.id)
                        break
                    elif sub_contract.end_date:
                        sub_end_date = sub_contract.end_date
                        sub_start_date = sub_contract.start_date
                        if (
                            sub_contract.end_reason_id == depart
                            or sub_end_date > sub_start_date + timedelta(days=50)
                        ):
                            sub_accept_ids.append(contract.id)
                            break
                    else:
                        sub_ids.append(contract.id)
                        break
                else:
                    sub_reject_ids.append(contract.id)

        return no_sub_ids, sub_ids, sub_accept_ids, sub_reject_ids, sub_waiting_ids
