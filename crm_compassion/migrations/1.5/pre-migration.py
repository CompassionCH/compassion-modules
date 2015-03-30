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


def update_projects(cr):
    """" Projects have now only one type for events. """
    cr.execute("UPDATE project_project SET project_type = 'event' "
               "WHERE project_type IN ('stand','concert','presentation',"
               "                       'meeting','sport')")


def update_analytic_accounts(cr):
    """ Change the naming scheme of the analytic accounts. """
    cr.execute("SELECT id from account_analytic_account "
               "WHERE name = 'Events'")
    root_id = cr.fetchone()[0]
    # Find all analytic accounts related to events projects
    cr.execute(
        "SELECT p.analytic_account_id as account_id, p.id as project_id, "
        "       e.type, e.start_date "
        "FROM project_project p JOIN crm_event_compassion e ON "
        "   p.id=e.project_id")
    res_query = cr.dictfetchall()
    analytic_ids = [str(r['account_id']) for r in res_query]
    cr.execute(
        "SELECT currency_id, user_id, name, date_start, company_id, state, "
        "       manager_id, type, use_timesheets, use_tasks, code "
        "FROM account_analytic_account WHERE id IN ({0})".format(
            ','.join(analytic_ids)))
    proj_event_analytic_data = cr.dictfetchall()

    # Create a Root Analytic Account for each Project
    for analytic_data in proj_event_analytic_data:
        # Change the reference of the account
        analytic_data['code'] = 'P' + analytic_data['code']
        columns = ','.join(analytic_data.keys()) + ',parent_id'
        values = ','.join(['%s' for v in range(
            0, len(analytic_data))]) + ',' + str(root_id)
        cr.execute(
            "INSERT INTO account_analytic_account({0}) VALUES ({1})".format(
                columns, values), analytic_data.values())

    # Attach old analytic accounts to the roots accounts created and update
    # the data.
    event_types = [r['type'].title() for r in res_query]
    event_years = [r['start_date'][:4] for r in res_query]
    for i in range(0, len(analytic_ids)):
        cr.execute(
            "UPDATE account_analytic_account a SET parent_id = ("
            "   SELECT max(id) from account_analytic_account "
            "   WHERE name = a.name AND id != a.id GROUP BY name), "
            "name = CONCAT('{0} / {1} / ', name), "
            "type = 'event' "
            "WHERE id = {2}".format(event_years[i], event_types[i],
                                    analytic_ids[i]))

    # Attach Projects to new analytic accounts
    proj_ids = [str(r['project_id']) for r in res_query]
    cr.execute(
        "UPDATE project_project p SET analytic_account_id = ("
        "   SELECT a.parent_id from account_analytic_account a "
        "   WHERE a.id = p.analytic_account_id) "
        "WHERE id IN ({0})".format(','.join(proj_ids)))


def migrate(cr, version):
    if not version:
        return

    # Change type of projects to event_id
    update_projects(cr)

    # Restructure analytic accounts
    update_analytic_accounts(cr)
