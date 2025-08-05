from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    for event in env["crm.event.compassion"].search([("lead_id", "!=", False)]):
        event.with_context(no_calendar=True).write(
            {
                "lead_ids": [(4, event.lead_id.id)],
                "lead_id": False,
            }
        )
