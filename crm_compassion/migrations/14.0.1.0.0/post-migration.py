from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Reload noupdate data
    openupgrade.load_data(
        env.cr, "crm_compassion", "security/crm_compassion_security.xml"
    )

    # Recompute balances
    env["crm.event.compassion"].search([]).with_context(
        dont_notify=True)._compute_balance()
