# Move the analytic accounts of events to the plan Events, then recompute the
# stored expense totals, which crm_compassion 18.0.1.0.0 could not find (T3511).
import logging
from collections import defaultdict

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL, float_compare

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    events = env["crm.event.compassion"].search([("analytic_id", "!=", False)])
    _move_accounts_to_events_plan(env, events.analytic_id)
    _recompute_expenses(env, events)


def _move_accounts_to_events_plan(env, accounts):
    """Write plan_id through the ORM so Odoo also moves the analytic lines of
    the accounts to the column of the plan Events."""
    line_obj = env["account.analytic.line"]
    events_plan = env.ref("crm_compassion.plan_events")
    events_fname = events_plan._column_name()
    to_move = accounts.filtered(lambda a: a.root_plan_id != events_plan)
    blocked = _accounts_blocking_move(env, to_move, events_fname)
    if blocked:
        _logger.warning(
            "%s event accounts not moved to Events: some of their lines would hold "
            "two accounts in the column of Events. Accounts (lines): %s",
            len(blocked),
            dict(sorted(blocked.items())),
        )
        to_move -= to_move.browse(blocked)
    to_move.write({"plan_id": events_plan.id})
    _logger.info("%s event accounts moved to the plan Events", len(to_move))

    _logger.info(
        "%s analytic lines of event accounts in the column of Events",
        line_obj.search_count([(events_fname, "in", accounts.ids)]),
    )
    project_plan, _other_plans = env["account.analytic.plan"]._get_all_plans()
    not_project = accounts.filtered(lambda a: a.root_plan_id != project_plan)
    stale = line_obj.search_count([("account_id", "in", not_project.ids)])
    if stale:
        _logger.warning(
            "%s analytic lines of event accounts are still in account_id, the "
            "column of the project plan, where Odoo's analytic reports do not "
            "find them. The migration chain's line move (18-pre-migration.sql) "
            "did not run on this database.",
            stale,
        )
    else:
        _logger.info("0 analytic lines of event accounts left in account_id")


def _accounts_blocking_move(env, accounts, events_fname):
    """{account id: number of lines} for the accounts Odoo cannot move to the
    column of Events: a line would get two accounts there, two of the moved
    accounts or a moved account and the one already there. Odoo refuses such
    a move (RedirectWarning) or overwrites the account of an earlier batch."""
    ids_by_fname = defaultdict(list)
    for account in accounts:
        ids_by_fname[account.plan_id._column_name()].append(account.id)
    if not ids_by_fname:
        return {}
    columns = [(SQL.identifier(fname), ids) for fname, ids in ids_by_fname.items()]
    env.flush_all()
    env.cr.execute(
        SQL(
            """
            SELECT acc.id, COUNT(*)
              FROM (
                    SELECT array_remove(ARRAY[%(moved)s], NULL) AS moved,
                           %(events_column)s AS target
                      FROM account_analytic_line
                     WHERE %(in_any_column)s
                   ) AS line
             CROSS JOIN unnest(line.moved) AS acc(id)
             WHERE cardinality(line.moved) > 1
                OR line.target != ALL(line.moved)
             GROUP BY acc.id
            """,
            moved=SQL(", ").join(
                SQL("CASE WHEN %s = ANY(%s) THEN %s END", column, ids, column)
                for column, ids in columns
            ),
            events_column=SQL.identifier(events_fname),
            in_any_column=SQL(" OR ").join(
                SQL("%s = ANY(%s)", column, ids) for column, ids in columns
            ),
        )
    )
    return dict(env.cr.fetchall())


def _recompute_expenses(env, events):
    before = {event.id: event.total_expense for event in events}
    env.add_to_compute(events._fields["total_expense"], events)
    events.modified(["total_expense"])
    env.flush_all()
    changed = events.filtered(
        lambda e: float_compare(e.total_expense, before[e.id], precision_digits=2)
    )
    _logger.info(
        "total_expense recomputed for %s events: %s changed, net difference %.2f",
        len(events),
        len(changed),
        sum(event.total_expense - before[event.id] for event in changed),
    )
