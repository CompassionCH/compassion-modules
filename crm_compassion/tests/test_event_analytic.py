##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEventAnalytic(TransactionCase):
    """The event of a donation (T3491) and the expenses of an event (T3511) are
    found from the event's analytic account, whatever its analytic plan."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        now = datetime.now()
        cls.event = cls.env["crm.event.compassion"].create(
            {
                "name": "Analytic plan test event",
                "type": "sport",
                "start_date": now,
                "end_date": now + timedelta(days=1),
                "hold_start_date": now.date(),
                "user_id": cls.env.uid,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Analytic plan donor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Analytic plan donation", "type": "service"}
        )

    def _donation_line(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "price_unit": 30,
                            "analytic_distribution": {
                                str(self.event.analytic_id.id): 100
                            },
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice.invoice_line_ids

    def test_event_in_events_plan(self):
        self.assertEqual(
            self.event.analytic_id.plan_id,
            self.env.ref("crm_compassion.plan_events"),
        )
        self.assertEqual(self._donation_line().event_id, self.event)

    def test_event_in_other_plan(self):
        """Accounts of events migrated from v14 are in another plan."""
        legacy_plan = self.env["account.analytic.plan"].create(
            {"name": "Analytic plan test legacy"}
        )
        self.event.analytic_id.plan_id = legacy_plan
        self.assertEqual(self._donation_line().event_id, self.event)

    def _expense_bill_line(self, amount):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "price_unit": amount,
                            "tax_ids": [Command.clear()],
                            "analytic_distribution": {
                                str(self.event.analytic_id.id): 100
                            },
                        }
                    )
                ],
            }
        )
        bill.action_post()
        return bill.invoice_line_ids

    def _analytic_line(self, amount):
        account = self.event.analytic_id
        return self.env["account.analytic.line"].create(
            {
                "name": "Analytic plan test line",
                "amount": amount,
                account.plan_id._column_name(): account.id,
            }
        )

    def _assert_expenses(self, expense_lines, total):
        self.env.invalidate_all()
        self.assertEqual(self.event.expense_line_ids, expense_lines)
        self.assertAlmostEqual(self.event.total_expense, total)
        self.assertAlmostEqual(self.event.balance, self.event.total_income - total)
        domain = self.event.show_expenses()["domain"]
        self.assertEqual(
            self.env["account.move.line"].search(domain),
            expense_lines.move_line_id,
        )

    def test_expenses_in_other_plan(self):
        """Expenses are found before and after the event moves its account
        from a migrated plan to the plan Events."""
        legacy_plan = self.env["account.analytic.plan"].create(
            {"name": "Analytic plan test legacy"}
        )
        account = self.event.analytic_id
        account.plan_id = legacy_plan
        bill_expense = self._expense_bill_line(100).analytic_line_ids
        manual_expense = self._analytic_line(-20)
        self._analytic_line(50)
        self.assertEqual(bill_expense[legacy_plan._column_name()], account)
        self._assert_expenses(bill_expense | manual_expense, 120)

        self.event.write({"name": "Analytic plan test event moved"})
        events_plan = self.env.ref("crm_compassion.plan_events")
        self.assertEqual(account.plan_id, events_plan)
        self.assertEqual(bill_expense[events_plan._column_name()], account)
        self._assert_expenses(bill_expense | manual_expense, 120)

    def test_total_expense_follows_lines(self):
        line = self._analytic_line(-30)
        self._assert_expenses(line, 30)

        line.amount = -45
        self._assert_expenses(line, 45)

        other_account = self.env["account.analytic.account"].create(
            {
                "name": "Analytic plan test other",
                "plan_id": self.event.analytic_id.plan_id.id,
            }
        )
        fname = self.event.analytic_id.plan_id._column_name()
        line[fname] = other_account
        self._assert_expenses(self.env["account.analytic.line"], 0)

        line[fname] = self.event.analytic_id
        self._assert_expenses(line, 45)

        line.unlink()
        self._assert_expenses(self.env["account.analytic.line"], 0)
