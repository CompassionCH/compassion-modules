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


def migrate(cr, version):
    if not version:
        return
    # Modify analytic accounts linked to Events to change their event type
    # and remove type and year from the name.
    cr.execute(
        """
        UPDATE account_analytic_account a
        SET event_type = lower((
            SELECT name from account_analytic_account WHERE id = (
                SELECT parent_id from account_analytic_account
                WHERE id = a.parent_id))),
        name = regexp_replace(name, '20(\d){2}', '')
        WHERE type = 'event'
        """)

    # Remove years from events
    # Set events to use takss (they all have a project before migration)
    # and set parent_id of events.
    cr.execute(
        """
        UPDATE crm_event_compassion e
        SET name = regexp_replace(name, '20(\d){2}', ''),
        use_tasks = TRUE,
        parent_id = (
            SELECT parent_id from account_analytic_account
            WHERE id = e.analytic_id)
        """)
