# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Therp BV (<http://therp.nl>).
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys


def migrate(cr, version):
    if not version:
        return
    # Modify analytic accounts linked to Events to change their event type
    # and remove type and year from the name.
    cr.execute(
        """
        UPDATE account_analytic_account
        SET event_type = lower(substring(name FROM '(?:.)*/ ((.)*) /(?:.)*')),
        name = substring(name FROM '(?:.)* / ((.)*$)')
        WHERE type = 'event'
        """)

    # Remove years from events
    cr.execute(
        """
        UPDATE crm_event_compassion
        SET name = regexp_replace(name, '20(\d){2}', '')
        """)

    # Add project task types
    cr.execute(
        """
        SELECT p.id as project_id, e.name as event_name, e.id as event_id
        FROM crm_event_compassion e JOIN project_project p
        ON e.project_id = p.id
        """)
    to_update = cr.fetchall()
    cr.execute(
        'DELETE FROM project_task_type_rel '
        'WHERE project_id IN ({0}) '.format(
            ','.join([str(r[0]) for r in to_update])
        ))
    reload(sys)
    sys.setdefaultencoding('UTF8')
    for data in to_update:
        cr.execute(
            "INSERT INTO project_task_type(name,state,description,sequence) "
            "VALUES ('{0}','open',CONCAT("
            "   'Task type generated for event ID ', {1}),1) ".format(
                data[1].replace('\'', '\'\''), data[2]))

        cr.execute("SELECT MAX(id) FROM project_task_type")
        task_type_id = cr.fetchone()[0]

        cr.execute(
            'INSERT INTO project_task_type_rel(project_id, type_id) '
            'VALUES ({0}, {1})'.format(data[0], task_type_id))
