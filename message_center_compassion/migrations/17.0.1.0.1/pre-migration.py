from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "message_center_compassion.notification_settings",
            "message_center_compassion.gmc_settings",
        ],
        True,
    )
