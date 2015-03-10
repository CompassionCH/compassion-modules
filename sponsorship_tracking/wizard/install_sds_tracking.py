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

    # Only at module installation
    def _set_sds_state(self, cr, uid, ids=None, context=None):
        contract_obj = self.pool.get('recurring.contract')
        active_contract_ids = contract_obj.search(
            cr, uid,
            [('state', 'in', ['waiting', 'active', 'mandate'])],
            context)
        draft_contract_ids = contract_obj.search(
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
        compassion_project_obj = self.pool.get('compassion.project')
        contract_obj = self.pool.get('recurring.contract')
        suspended_project_ids = compassion_project_obj.search(
            cr, uid, [('status', '=', 'S')], context=context)
        suspended_project_contract_ids = contract_obj.search(
            cr, uid,
            [('project_id', 'in', suspended_project_ids),
             ('state', 'not in', ['terminated', 'cancelled'])],
            context)

        active_project_ids = compassion_project_obj.search(
            cr, uid, [('status', '=', 'A')], context=context)
        active_project_contract_ids = contract_obj.search(
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
