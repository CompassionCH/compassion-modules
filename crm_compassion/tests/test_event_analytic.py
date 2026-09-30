##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEventAnalytic(TransactionCase):
    """The event of a donation is found from its analytic account, whatever
    the analytic plan of the account (T3491)."""

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
