##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestArchiveAnalyticAccounts(TransactionCase):
    """The accounts of finished interventions without balance nor recent
    movement are archived."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.plan = cls.env["account.analytic.plan"].create(
            {"name": "Archive test interventions"}
        )
        cls.number = 0

    def _intervention(self, end_years=None, start_years=None, **vals):
        type(self).number += 1
        account = self.env["account.analytic.account"].create(
            {"name": f"Archive test INT-{self.number}", "plan_id": self.plan.id}
        )
        Intervention = self.env["compassion.intervention"]
        with patch.object(type(Intervention), "get_infos"):
            return Intervention.create(
                {
                    "name": f"Archive test {self.number}",
                    "intervention_id": f"ARCHIVE-TEST-{self.number}",
                    "service_level": "Level 1",
                    "analytic_account_id": account.id,
                    "end_date": end_years
                    and self.today - relativedelta(years=end_years),
                    "start_date": start_years
                    and self.today - relativedelta(years=start_years),
                    **vals,
                }
            )

    def _line(self, account, amount, years_ago):
        self.env["account.analytic.line"].create(
            {
                "name": "Archive test",
                "amount": amount,
                "date": self.today - relativedelta(years=years_ago),
                self.plan._column_name(): account.id,
            }
        )

    def _archive(self):
        self.env["compassion.intervention"]._cron_archive_finished_analytic_accounts()

    def test_finished_without_balance_archived(self):
        ended = self._intervention(end_years=3)
        self._line(ended.analytic_account_id, 100, 3)
        self._line(ended.analytic_account_id, -100, 3)
        started = self._intervention(start_years=4)
        self._archive()
        self.assertFalse(ended.analytic_account_id.active)
        self.assertFalse(started.analytic_account_id.active)

    def test_not_finished_kept(self):
        recent_end = self._intervention(end_years=1)
        recent_start = self._intervention(start_years=2)
        no_date = self._intervention()
        self._archive()
        self.assertTrue(recent_end.analytic_account_id.active)
        self.assertTrue(recent_start.analytic_account_id.active)
        self.assertTrue(no_date.analytic_account_id.active)

    def test_balance_or_recent_movement_kept(self):
        with_balance = self._intervention(end_years=3)
        self._line(with_balance.analytic_account_id, 100, 3)
        recent = self._intervention(end_years=3)
        self._line(recent.analytic_account_id, 100, 1)
        self._line(recent.analytic_account_id, -100, 1)
        self._archive()
        self.assertTrue(with_balance.analytic_account_id.active)
        self.assertTrue(recent.analytic_account_id.active)

    def test_shared_account_waits_for_all(self):
        ended = self._intervention(end_years=3)
        running = self._intervention(
            end_years=1, analytic_account_id=ended.analytic_account_id.id
        )
        self._archive()
        self.assertTrue(running.analytic_account_id.active)
