from openupgradelib import openupgrade

xml_ids = ["action_sub_check"]


def migrate(cr, version):
    cr.execute(
        """
        SELECT id FROM ir_act_server WHERE base_automation_id = ANY (
            SELECT res_id FROM ir_model_data WHERE model = 'base.automation'
            AND module = 'sponsorship_sub_management'
        )
    """
    )
    res_ids = [r[0] for r in cr.fetchall()]
    for xml_id, res_id in zip(xml_ids, res_ids, strict=True):
        openupgrade.add_xmlid(
            cr, "sponsorship_sub_management", xml_id, "ir.actions.server", res_id
        )
