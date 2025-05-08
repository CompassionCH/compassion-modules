from openupgradelib import openupgrade

xml_ids = [
    "action_intervention_active",
    "action_intervention_close",
    "action_sla_done",
    "action_sla_wait",
    "action_notify_before_expire",
]


def migrate(cr, version):
    cr.execute(
        """
        SELECT id FROM ir_act_server WHERE base_automation_id = ANY (
            SELECT res_id FROM ir_model_data WHERE model = 'base.automation'
            AND module = 'intervention_compassion'
        )"""
    )
    res_ids = [r[0] for r in cr.fetchall()]
    if len(res_ids) == len(xml_ids):
        for xml_id, res_id in zip(xml_ids, res_ids, strict=True):
            openupgrade.add_xmlid(
                cr, "intervention_compassion", xml_id, "ir.actions.server", res_id
            )
