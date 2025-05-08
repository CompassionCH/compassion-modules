from openupgradelib import openupgrade


def migrate(cr, version):
    if openupgrade.column_exists(cr, "res_partner", "uuid"):
        cr.execute(
            """
                  WITH UUIDCounts AS (
            SELECT uuid, COUNT(*) as count
            FROM res_partner
            GROUP BY uuid
            HAVING COUNT(*) > 1
        ),
        RowsToUpdate AS (
            SELECT rp.id
            FROM res_partner rp
            JOIN UUIDCounts uc ON rp.uuid = uc.uuid
            WHERE uc.count > 1
        )
        UPDATE res_partner
        SET uuid = gen_random_uuid()
        WHERE id IN (SELECT id FROM RowsToUpdate);
        """
        )
