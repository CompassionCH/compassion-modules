##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import importlib.util
from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

LOGGER = "crm_compassion_post_migration_18_0_1_0_1"


def _load_post_migration():
    path = file_path("crm_compassion/migrations/18.0.1.0.1/post-migration.py")
    spec = importlib.util.spec_from_file_location(LOGGER, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestMigrationExpenses(TransactionCase):
    """18.0.1.0.1 post-migration: event accounts move to the plan Events and
    the expense totals are recomputed (T3511)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.migration = _load_post_migration()
        plan_obj = cls.env["account.analytic.plan"]
        cls.events_plan = cls.env.ref("crm_compassion.plan_events")
        cls.legacy = plan_obj.create({"name": "Migration test legacy"})
        cls.legacy_child = plan_obj.create(
            {"name": "Migration test legacy child", "parent_id": cls.legacy.id}
        )
        cls.events_child = plan_obj.create(
            {"name": "Migration test events child", "parent_id": cls.events_plan.id}
        )
        cls.legacy_col = cls.legacy._column_name()
        cls.events_col = cls.events_plan._column_name()

    def _event(self, name, plan):
        now = datetime.now()
        event = self.env["crm.event.compassion"].create(
            {
                "name": name,
                "type": "sport",
                "start_date": now,
                "end_date": now + timedelta(days=1),
                "hold_start_date": now.date(),
                "user_id": self.env.uid,
            }
        )
        event.analytic_id.plan_id = plan
        return event

    def _line(self, amount, **accounts):
        return self.env["account.analytic.line"].create(
            {
                "name": "Migration test line",
                "amount": amount,
                **{column: account.id for column, account in accounts.items()},
            }
        )

    def test_move_accounts(self):
        plain = self._event("Plain", self.legacy)
        child = self._event("Child", self.legacy_child)
        blocked = self._event("Blocked", self.legacy)
        same_batch = self._event("Same batch", self.legacy)
        in_events = self._event("Events child", self.events_child)
        other = self.env["account.analytic.account"].create(
            {"name": "Migration test other", "plan_id": self.events_plan.id}
        )
        plain_line = self._line(-10, **{self.legacy_col: plain.analytic_id})
        child_line = self._line(-20, **{self.legacy_col: child.analytic_id})
        self._line(
            -30, **{self.legacy_col: blocked.analytic_id, self.events_col: other}
        )
        # A line of one event account holding another event account of the
        # same batch in the column of Events: neither may be overwritten.
        shared_line = self._line(
            -40,
            **{
                self.legacy_col: same_batch.analytic_id,
                self.events_col: plain.analytic_id,
            },
        )
        accounts = (plain | child | blocked | same_batch | in_events).analytic_id

        with self.assertLogs(LOGGER, "INFO") as logs:
            self.migration._move_accounts_to_events_plan(self.env, accounts)

        self.assertEqual(plain.analytic_id.plan_id, self.events_plan)
        self.assertEqual(child.analytic_id.plan_id, self.events_plan)
        self.assertEqual(blocked.analytic_id.plan_id, self.legacy)
        self.assertEqual(same_batch.analytic_id.plan_id, self.legacy)
        self.assertEqual(in_events.analytic_id.plan_id, self.events_child)
        self.assertEqual(plain_line[self.events_col], plain.analytic_id)
        self.assertEqual(child_line[self.events_col], child.analytic_id)
        self.assertFalse(child_line[self.legacy_col])
        self.assertEqual(shared_line[self.legacy_col], same_batch.analytic_id)
        self.assertEqual(shared_line[self.events_col], plain.analytic_id)
        output = "\n".join(logs.output)
        self.assertIn(
            "2 event accounts of plan Migration test legacy not moved", output
        )
        self.assertIn("2 event accounts moved to the plan Events", output)
        self.assertIn("0 analytic lines of event accounts left in account_id", output)

    def test_accounts_sharing_a_line(self):
        """Two moved accounts on one line would make Odoo refuse the second
        move: both stay in their plan, the others move."""
        legacy_2 = self.env["account.analytic.plan"].create(
            {"name": "Migration test legacy 2"}
        )
        first = self._event("First", self.legacy)
        second = self._event("Second", legacy_2)
        alone = self._event("Alone", self.legacy)
        line = self._line(
            -10,
            **{
                self.legacy_col: first.analytic_id,
                legacy_2._column_name(): second.analytic_id,
            },
        )
        self._line(-20, **{self.legacy_col: alone.analytic_id})
        accounts = (first | second | alone).analytic_id

        with self.assertLogs(LOGGER, "WARNING") as logs:
            self.migration._move_accounts_to_events_plan(self.env, accounts)

        self.assertEqual(first.analytic_id.plan_id, self.legacy)
        self.assertEqual(second.analytic_id.plan_id, legacy_2)
        self.assertEqual(alone.analytic_id.plan_id, self.events_plan)
        self.assertEqual(line[self.legacy_col], first.analytic_id)
        self.assertEqual(line[legacy_2._column_name()], second.analytic_id)
        self.assertFalse(line[self.events_col])
        self.assertIn("2 event accounts not moved to Events", logs.output[0])

    def test_lines_left_in_account_id(self):
        event = self._event("Left in account_id", self.legacy)
        self._line(-10, account_id=event.analytic_id)
        with self.assertLogs(LOGGER, "WARNING") as logs:
            self.migration._move_accounts_to_events_plan(self.env, event.analytic_id)
        self.assertIn(
            "1 analytic lines of event accounts are still in account_id", logs.output[0]
        )

    def test_recompute_expenses(self):
        event = self._event("Recompute", self.events_plan)
        self._line(-70, **{self.events_col: event.analytic_id})
        self._line(15, **{self.events_col: event.analytic_id})
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE crm_event_compassion SET total_expense = 5, balance = -5 "
            "WHERE id = %s",
            [event.id],
        )
        self.env.invalidate_all()

        with self.assertLogs(LOGGER, "INFO") as logs:
            self.migration._recompute_expenses(self.env, event)

        self.assertEqual(event.total_expense, 70)
        self.assertEqual(event.balance, event.total_income - 70)
        self.assertIn("1 changed, net difference 65.00", logs.output[0])
