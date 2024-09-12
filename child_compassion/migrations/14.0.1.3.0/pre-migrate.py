from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM compassion_child_pictures ccp
        WHERE ccp.id in (
            SELECT ccp_duppl.id FROM (
                SELECT id, row_number() OVER(
                    PARTITION BY child_id, image_url ORDER BY date ASC) AS row_num
                FROM compassion_child_pictures) ccp_duppl
                WHERE ccp_duppl.row_num > 1)
        """,
    )
