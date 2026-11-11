from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGiftFromPayment(TransactionCase):
    """Runs on a database with real sponsorships (no demo data needed)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, no_upsert=True))
        cls.gift_obj = cls.env["sponsorship.gift"]
        cls.gift_type = cls.env["sponsorship.gift.type"].search(
            [("product_id", "!=", False)], limit=1
        )
        cls.sponsorship = cls.env["recurring.contract"].search(
            [
                ("state", "=", "active"),
                ("child_id", "!=", False),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        cls.partner_1 = cls.sponsorship.gift_partner_id

    def setUp(self):
        super().setUp()
        if not self.gift_type or not self.sponsorship:
            self.skipTest("Needs an active sponsorship and a gift type with product")
        # Start from a sponsorship without pending gifts of that type
        self.gift_obj.search(
            [
                ("sponsorship_id", "=", self.sponsorship.id),
                ("gift_type_id", "=", self.gift_type.id),
                ("state", "in", ["draft", "verify"]),
            ]
        ).write({"state": "Undeliverable"})

    def _gift_vals(self, **kwargs):
        vals = {
            "sponsorship_id": self.sponsorship.id,
            "gift_type_id": self.gift_type.id,
            "amount": 10.0,
            "gift_date": "2026-11-10",
        }
        vals.update(kwargs)
        return vals

    def _create_payment_line(self, instructions):
        company = self.env.company
        income = self.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_ids", "in", company.id),
            ],
            limit=1,
        )
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": journal.default_account_id.id or income.id,
                            "debit": 10.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": income.id,
                            "partner_id": self.partner_1.id,
                            "credit": 10.0,
                            "product_id": self.gift_type.product_id.id,
                            "contract_id": self.sponsorship.id,
                            "gift_instructions": instructions,
                        },
                    ),
                ],
            }
        )
        return move.line_ids.filtered("credit")

    def test_merge_pending_gift_without_instructions(self):
        """A second pending gift for the same sponsorship, type and year is
        merged into the first one, even when no message is given."""
        first = self.gift_obj.create(self._gift_vals(instructions="Happy birthday"))
        second = self.gift_obj.create(self._gift_vals())
        self.assertEqual(second, first)
        self.assertEqual(first.amount, 20.0)
        self.assertEqual(first.instructions, "Happy birthday")

    def test_gift_message_from_payment_line(self):
        """The gift created from a payment line gets the line's message, and
        a second payment adds its message to the pending gift."""
        line = self._create_payment_line("Happy birthday")
        gift = self.gift_obj.create_from_invoice_line(line.id)
        self.assertEqual(gift.instructions, "Happy birthday")
        self.assertEqual(gift.invoice_line_ids, line)

        other_line = self._create_payment_line("God bless you")
        merged = self.gift_obj.create_from_invoice_line(other_line.id)
        self.assertEqual(merged, gift)
        self.assertEqual(gift.instructions, "Happy birthday; God bless you")
        self.assertEqual(gift.invoice_line_ids, line + other_line)
