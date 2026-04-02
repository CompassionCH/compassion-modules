from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # List of XML IDs to be removed
    obsolete_xml_ids = [
        "project_suspension_e1",
        "project_suspension_e2",
        "project_reactivation",
    ]

    for xml_id in obsolete_xml_ids:
        # ref() finds the database record using the XML ID
        record = env.ref(
            f"partner_communication_compassion.{xml_id}", raise_if_not_found=False
        )

        if record:
            # 1. Find and delete all communication logs linked to this config
            logs = env["partner.communication.job"].search(
                [("config_id", "=", record.id)]
            )
            if logs:
                logs.write(
                    {"config_id": 1}
                )  # Set to Default config (ID=1) to avoid orphaned logs

            # 2. Delete the config record itself
            record.unlink()
