# Move the analytic accounts of events to the plan Events, then recompute the
# stored expense totals, which crm_compassion 18.0.1.0.0 could not find (T3511).
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import float_compare

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
    # Odoo refuses the move (RedirectWarning) if a line already holds another
    # account in the column of Events: leave these accounts in their plan.
    for plan, plan_accounts in to_move.grouped("plan_id").items():
        fname = plan._column_name()
        conflicts = line_obj.search(
            [
                (events_fname, "not in", plan_accounts.ids + [False]),
                (fname, "in", plan_accounts.ids),
            ]
        )
        if conflicts:
            blocked = conflicts.mapped(fname)
            _logger.warning(
                "%s event accounts of plan %s not moved to Events: %s of their "
                "lines already have an account of Events. Accounts: %s",
                len(blocked),
                plan.name,
                len(conflicts),
                blocked.ids,
            )
            to_move -= blocked
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
