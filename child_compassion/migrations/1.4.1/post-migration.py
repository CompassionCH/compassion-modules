# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import sys


def migrate(cr, version):
    reload(sys)
    sys.setdefaultencoding('UTF8')

    if not version:
        return
    # Add translated value for new property distance_from_closest_city
    # based on old string distance_from_closest_city

    cr.execute(
        """
        CREATE RULE "my_table_on_duplicate_ignore"
        AS ON INSERT TO "compassion_translated_value"
        WHERE EXISTS(SELECT 1 FROM compassion_translated_value
                    WHERE value_en=NEW.value_en)
        DO INSTEAD NOTHING;
        INSERT INTO compassion_translated_value
        (is_tag,value_en, property_name)
        SELECT False, distance_from_closest_city, 'distance_from_closest_city'
        FROM compassion_project
        WHERE distance_from_closest_city IS NOT NULL;
        DROP RULE "my_table_on_duplicate_ignore"
        ON "compassion_translated_value";
        """)

    cr.execute(
        'SELECT id, distance_from_closest_city '
        'FROM compassion_project '
        'WHERE distance_from_closest_city IS NOT NULL'
    )
    projects = cr.fetchall()

    cr.execute(
        '''
        CREATE RULE "my_table_on_duplicate_ignore"
        AS ON INSERT TO "project_property_to_value"
        WHERE EXISTS(SELECT 1 FROM project_property_to_value
                    WHERE value_id=NEW.value_id
                    AND project_id = NEW.project_id)
        DO INSTEAD NOTHING;
        ''')

    for project in projects:
        cr.execute(
            "SELECT id FROM compassion_translated_value "
            "WHERE value_en = '{}'".format(project[1].replace('\'', '\'\'')))
        translated_value_id = cr.fetchall()[0][0]

        cr.execute(
            "INSERT INTO project_property_to_value (project_id, value_id) "
            "VALUES ({0},{1})".format(
                project[0], translated_value_id))

    cr.execute(
        """
        DROP RULE "my_table_on_duplicate_ignore"
        ON "project_property_to_value";
        """)
