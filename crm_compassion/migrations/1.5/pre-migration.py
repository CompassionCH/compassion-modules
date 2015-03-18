# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
logger = logging.getLogger()


def rename_columns(cr, column_spec):
    """
    Rename table columns. Taken from OpenUpgrade.

    :param column_spec: a hash with table keys, with lists of tuples as \
    values. Tuples consist of (old_name, new_name).

    """
    for table in column_spec.keys():
        for (old, new) in column_spec[table]:
            logger.info("table %s, column %s: renaming to %s", table, old,
                        new)
            cr.execute('ALTER TABLE %s RENAME %s TO %s' % (table, old, new))
            cr.execute('DROP INDEX IF EXISTS "%s_%s_index"' % (table, old))


def update_projects(cr):
    """" Projects have now only one type for events. """
    cr.execute("UPDATE project_project SET project_type = 'event' "
               "WHERE project_type IN ('stand','concert','presentation',"
               "                       'meeting','sport')")
            
def migrate(cr, version):
    if not version:
        return

    # rename field event_id so that it is not deleted
    rename_columns(cr, {
        'crm_lead': [
            ('event_id', 'old_event_id'),
        ]
    })
    
    # change type of projects to event_id
    update_projects(cr)
