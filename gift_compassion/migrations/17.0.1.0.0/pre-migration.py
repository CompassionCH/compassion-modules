from openupgradelib import openupgrade

xml_ids = ["action_enable_postponed_gifts"]
module = "gift_compassion"


def migrate(cr, version):
    cr.execute(
        """
        SELECT id FROM ir_act_server WHERE base_automation_id = ANY (
            SELECT res_id FROM ir_model_data WHERE model = 'base.automation'
            AND module = %s
        )
    """,
        [module],
    )
    res_ids = [r[0] for r in cr.fetchall()]
    if len(res_ids) == len(xml_ids):
        for xml_id, res_id in zip(xml_ids, res_ids, strict=True):
            openupgrade.add_xmlid(cr, module, xml_id, "ir.actions.server", res_id)
