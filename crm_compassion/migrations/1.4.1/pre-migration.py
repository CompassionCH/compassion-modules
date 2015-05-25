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


def update_analytic_accounts(cr):
    """ Change the type of the analytic accounts. """
    # Find all analytic accounts related to events
    cr.execute(
        "SELECT p.analytic_account_id as account_id, p.id as project_id, "
        "       e.type, e.start_date "
        "FROM project_project p JOIN crm_event_compassion e ON "
        "   p.id=e.project_id")
    res_query = cr.dictfetchall()
    analytic_ids = [str(r['account_id']) for r in res_query]

    cr.execute(
        "UPDATE account_analytic_account a SET type = 'event' "
        "WHERE id in ({0})".format(','.join(analytic_ids)))


def migrate(cr, version):
    if not version:
        return

    # Change type of analytic accounts
    update_analytic_accounts(cr)
