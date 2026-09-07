from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if version:
        # Pre-create the column so Odoo's _auto_init (running after this
        # pre-migration, per odoo/modules/loading.py) finds it already
        # exists and does not schedule a recompute for existing rows -
        # matches odoo/tools/sql.py's own create_column for booleans.
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE correspondence
            ADD COLUMN IF NOT EXISTS on_hold boolean DEFAULT false
            """,
        )
