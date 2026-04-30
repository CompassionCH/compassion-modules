from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


def migrate(cr, version):
    openupgrade.logged_query(
        cr,
        """
        UPDATE compassion_child
        SET vocational_training_id = (
            SELECT id FROM child_vocational_training
            WHERE name = vocational_training_type
        )
        WHERE vocational_training_type IS NOT NULL;
            """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE compassion_child
        SET major_course_study_id = (SELECT id
                                     FROM child_major_course_study
                                     WHERE name = major_course_study)
        WHERE major_course_study IS NOT NULL;
    """,
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    path = "child_compassion/static/mappings/"
    files = ["child.json"]
    load_mapping_files(env, path, files)
