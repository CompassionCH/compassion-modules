from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    if not openupgrade.column_exists(cr, "child_disaster_impact", "child_global_id"):
        cr.execute("""
        ALTER TABLE child_disaster_impact
        ADD COLUMN child_global_id character varying
        """)
    if not openupgrade.column_exists(cr, "fcp_disaster_impact", "project_fcp_id"):
        cr.execute("""
        ALTER TABLE fcp_disaster_impact
        ADD COLUMN project_fcp_id character varying
        """)
    cr.execute("""
    UPDATE child_disaster_impact impact
    SET child_global_id = (
        SELECT global_id FROM compassion_child WHERE id = impact.child_id)
    """)
    cr.execute("""
    UPDATE fcp_disaster_impact impact
    SET project_fcp_id = (
        SELECT fcp_id FROM compassion_project WHERE id = impact.project_id)
    """)
