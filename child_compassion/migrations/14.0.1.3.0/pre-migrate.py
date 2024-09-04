from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM compassion_child_pictures ccp_a
        USING compassion_child_pictures cpp_b
        WHERE ccp_a.image_url == ccp_b.image_url 
            AND ccp_a.child_id == ccp_b.child_id AND ccp_a.date >= cpp_b.date;
        """,
    )
