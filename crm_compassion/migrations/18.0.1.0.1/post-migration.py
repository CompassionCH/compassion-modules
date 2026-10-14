# Move the analytic accounts of events to the plan Events, then recompute the
# stored expense totals, which crm_compassion 18.0.1.0.0 could not find (T3511).
import logging

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
    # A line that already holds another account in the column of Events would
    # make Odoo refuse the move (RedirectWarning), or overwrite that account
    # when it is moved in the same batch: leave such accounts in their plan.
    env.flush_all()
    for plan, plan_accounts in to_move.grouped("plan_id").items():
        fname = SQL.identifier(plan._column_name())
        env.cr.execute(
            SQL(
                """
                SELECT %(fname)s, COUNT(*)
                  FROM account_analytic_line
                 WHERE %(fname)s = ANY(%(ids)s)
                   AND %(events_fname)s IS NOT NULL
                   AND %(events_fname)s != %(fname)s
                 GROUP BY %(fname)s
                """,
                fname=fname,
                events_fname=SQL.identifier(events_fname),
                ids=plan_accounts.ids,
            )
        )
        conflicts = dict(env.cr.fetchall())
        if conflicts:
            _logger.warning(
                "%s event accounts of plan %s not moved to Events: %s of their "
                "lines already have another account of Events. Accounts: %s",
                len(conflicts),
                plan.name,
                sum(conflicts.values()),
                sorted(conflicts),
            )
            to_move -= to_move.browse(conflicts)
    # Two moved accounts on one line: Odoo moves the first into the column of
    # Events, then refuses the second (RedirectWarning). Leave both.
    shared = _accounts_sharing_lines(env, to_move)
    if shared:
        _logger.warning(
            "%s event accounts not moved to Events: some of their lines hold "
            "another event account to move. Accounts (lines): %s",
            len(shared),
            dict(sorted(shared.items())),
        )
        to_move -= to_move.browse(shared)
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


def _accounts_sharing_lines(env, accounts):
    """{account id: number of lines} for the accounts that share a line with
    another of the accounts, in the columns Odoo moves them from."""
    if not accounts:
        return {}
    columns = [
        SQL.identifier("line", fname)
        for fname in sorted({plan._column_name() for plan in accounts.plan_id})
    ]
    env.cr.execute(
        SQL(
            """
            SELECT acc.id, COUNT(*)
              FROM (
                    SELECT ARRAY(
                           SELECT DISTINCT unnest(ARRAY[%(columns)s])
                           INTERSECT SELECT unnest(%(ids)s::int[])
                           ) AS ids
                      FROM account_analytic_line line
                     WHERE %(in_any_column)s
                   ) AS line_accounts
             CROSS JOIN unnest(line_accounts.ids) AS acc(id)
             WHERE cardinality(line_accounts.ids) > 1
             GROUP BY acc.id
            """,
            columns=SQL(", ").join(columns),
            ids=accounts.ids,
            in_any_column=SQL(" OR ").join(
                SQL("%s = ANY(%s)", column, accounts.ids) for column in columns
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
