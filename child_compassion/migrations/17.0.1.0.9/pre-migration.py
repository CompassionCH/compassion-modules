from openupgradelib import openupgrade


def migrate(cr, version):
    if not openupgrade.column_exists(
        cr, "compassion_project", "gps_latitude_obfuscated"
    ):
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE compassion_project
            ADD COLUMN gps_latitude_obfuscated float,
            ADD COLUMN gps_longitude_obfuscated float;
            """,
        )
        openupgrade.logged_query(
            cr,
            """
    UPDATE compassion_project
    SET gps_longitude_obfuscated = TRUNC(CAST(gps_longitude AS numeric), 0),
        gps_latitude_obfuscated = TRUNC(CAST(gps_latitude AS numeric), 0);
""",
        )
