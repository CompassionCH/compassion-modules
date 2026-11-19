from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # T3417: the automation is noupdate, so it kept the action migrated from 14.0
    # (code "records.warn_admin", a no-op). Link the action from the data file.
    automation = env.ref(
        "survival_sponsorship_compassion.warn_admin_on_product_overload",
        raise_if_not_found=False,
    )
    action = env.ref(
        "survival_sponsorship_compassion.warn_admin_on_product_overload_action",
        raise_if_not_found=False,
    )
    if not (automation and action):
        return
    old_actions = automation.action_server_ids - action
    # Leftover 14.0 column, not used by 18.0, blocks the delete (ON DELETE RESTRICT)
    if openupgrade.column_exists(env.cr, "base_automation", "action_server_id"):
        env.cr.execute(
            "UPDATE base_automation SET action_server_id = NULL WHERE id = %s",
            (automation.id,),
        )
    automation.action_server_ids = [(6, 0, action.ids)]
    old_actions.unlink()
