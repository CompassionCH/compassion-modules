from openupgradelib import openupgrade


def migrate(cr, version):
    # Remove parameters from report paperformat (no longer used)
    openupgrade.logged_query(cr, "DELETE FROM report_paperformat_parameter;")
    if not openupgrade.column_exists(cr, "correspondence", "has_valid_language"):
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE correspondence
            ADD COLUMN has_valid_language boolean DEFAULT true;
            """,
        )
        openupgrade.logged_query(
            cr,
            """ALTER TABLE correspondence
        ALTER COLUMN has_valid_language
        SET DEFAULT false;""",
        )
