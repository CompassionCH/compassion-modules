from datetime import date

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Reload noupdate data
    openupgrade.load_data(
        env.cr, "crm_compassion", "security/crm_compassion_security.xml"
    )

    # Recompute balances
    env["crm.event.compassion"].search([]).with_context(
        dont_notify=True
    )._compute_balance()

    openupgrade.logged_query(
        env.cr,
        """
    UPDATE res_partner
    SET ambassador_receipt_send_mode = 'none'
    WHERE a.mail_copy_when_donation = false
    FROM advocate_details a
    WHERE a.partner_id = res_partner.id""",
    )
    config = env.ref("crm_compassion.config_event_standard")
    events = env["crm.event.compassion"].search(
        [
            ("type", "in", ["sport", "tour"]),
            ("end_date", ">", date.today()),
            ("communication_config_id", "=", False),
        ]
    )
    events.write({"communication_config_id": config.id})
