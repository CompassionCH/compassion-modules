import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Manual compute sponsorships count to speed up the module update
    if not openupgrade.column_exists(cr, "compassion_project", "sponsorships_count"):
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE compassion_project
            ADD COLUMN sponsorships_count integer
            """,
        )

    openupgrade.logged_query(
        cr,
        """
        UPDATE compassion_project
        SET sponsorships_count = (
            SELECT COUNT(*)
            FROM recurring_contract JOIN compassion_child
            ON recurring_contract.child_id = compassion_child.id
            WHERE project_id = compassion_project.id
            AND recurring_contract.state NOT IN ('cancelled', 'terminated')
        )
        """,
    )
