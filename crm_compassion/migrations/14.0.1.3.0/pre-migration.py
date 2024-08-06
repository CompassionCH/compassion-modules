from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE crm_stage
        SET is_lost = TRUE
        WHERE LOWER(name) LIKE '%lost%';
        """
    )