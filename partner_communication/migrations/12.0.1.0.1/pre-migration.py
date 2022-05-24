from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    # Remove noupdate
    openupgrade.set_xml_ids_noupdate_value(
        env, "partner_communication", ["communication_job_rule"], False)
