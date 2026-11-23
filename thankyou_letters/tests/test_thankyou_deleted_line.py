##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestThankYouDeletedLine(AccountTestInvoicingCommon):
    """A donation line can be deleted while its thank you is pending, e.g.
    when the bank statement line it was booked on is reconciled again. The
    thank you must then forget it, or its text can no longer be rendered.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["thankyou.config"].create(
            {"min_donation_amount": 0, "send_mode": "auto_digital_only"}
        )
        cls.donation = cls.env["product.product"].create(
            {"name": "Water for children", "lst_price": 200, "requires_thankyou": True}
        )

    def _donation_entry(self, *amounts):
        """Draft journal entry of donations, as booked from a bank statement."""
        income = self.company_data["default_account_revenue"]
        bank = self.company_data["default_journal_bank"].default_account_id
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": bank.id,
                            "partner_id": self.partner_a.id,
                            "debit": sum(amounts),
                        }
                    )
                ]
                + [
                    Command.create(
                        {
                            "account_id": income.id,
                            "partner_id": self.partner_a.id,
                            "product_id": self.donation.id,
                            "credit": amount,
                        }
                    )
                    for amount in amounts
                ],
            }
        )

    def _thank(self, move):
        lines = move.line_ids.filtered("product_id")
        comm_ids = lines.generate_thank_you()
        return lines, self.env["partner.communication.job"].browse(comm_ids)

    def _delete(self, line):
        """Delete a donation line, keeping its entry balanced."""
        bank_line = line.move_id.line_ids.filtered(lambda x: x.debit)
        line.move_id.write(
            {
                "line_ids": [
                    Command.delete(line.id),
                    Command.update(
                        bank_line.id, {"debit": bank_line.debit - line.credit}
                    ),
                ]
            }
        )

    def _dead_line_id(self):
        Line = self.env["account.move.line"]
        return Line.search([], order="id desc", limit=1).id + 1000

    def test_deleted_line_is_removed_from_thank_you(self):
        """Two donations booked on two entries share one thank you, then one
        of them is booked again (its line deleted)."""
        first, comm = self._thank(self._donation_entry(200))
        second, comm2 = self._thank(self._donation_entry(150))
        self.assertEqual(comm2, comm)
        self.assertEqual(comm.get_objects(), first | second)

        self._delete(second)

        self.assertTrue(comm.exists())
        self.assertEqual(comm.object_ids, str(first.id))
        self.assertEqual(comm.get_objects().get_donation_amount(), 200)
        # Rendering again no longer meets the deleted line
        comm.refresh_text()

    def test_deleted_line_of_thank_you_without_entry_pointer(self):
        """A communication can hold donation lines without their entries
        pointing to it, and be sent to someone else than the donor: thank
        you wizard, merge at creation, ambassador receipt (sent to the
        ambassador)."""
        lines = self._donation_entry(200, 100).line_ids.filtered("product_id")
        ambassador = self.partner_b
        self.assertNotEqual(ambassador.commercial_partner_id, self.partner_a)
        receipt = self.env["partner.communication.job"].create(
            {
                "partner_id": ambassador.id,
                "config_id": self.env.ref(
                    "thankyou_letters.config_thankyou_standard"
                ).id,
                "object_ids": lines.ids,
            }
        )
        self.assertFalse(lines.move_id.communication_id)

        self._delete(lines[0])

        self.assertEqual(receipt.object_ids, str(lines[1].id))

    def test_new_donation_drops_deleted_line_of_pending_thank_you(self):
        """A thank you already holding a deleted line (before this fix) is
        healed by the next donation instead of carrying the dead id."""
        first, comm = self._thank(self._donation_entry(200))
        dead_id = self._dead_line_id()
        # Set in SQL: writing it renders the text, which fails on the dead id
        self.env.cr.execute(
            "UPDATE partner_communication_job SET object_ids = %s WHERE id = %s",
            (f"{first.id},{dead_id}", comm.id),
        )
        comm.invalidate_recordset(["object_ids"])

        second, comm2 = self._thank(self._donation_entry(150))

        self.assertEqual(comm2, comm)
        self.assertEqual(comm.get_objects(), first | second)
        self.assertEqual(comm.get_objects().get_donation_amount(), 350)

    def test_new_donation_cancels_thank_you_of_deleted_lines_only(self):
        """A pending thank you of another config listing only deleted lines
        is cancelled by the next donation instead of blocking it."""
        old_lines, old_comm = self._thank(self._donation_entry(200))
        old_comm.config_id = self.env.ref(
            "thankyou_letters.config_thankyou_standard"
        ).copy()
        self.env.cr.execute(
            "UPDATE partner_communication_job SET object_ids = %s WHERE id = %s",
            (str(self._dead_line_id()), old_comm.id),
        )
        old_comm.invalidate_recordset(["object_ids"])

        lines, comm = self._thank(self._donation_entry(150))

        self.assertEqual(old_comm.state, "cancel")
        self.assertNotEqual(comm, old_comm)
        self.assertEqual(comm.get_objects(), lines)

    def test_thank_you_of_deleted_lines_is_removed(self):
        lines, comm = self._thank(self._donation_entry(200))
        lines.move_id.line_ids.unlink()
        self.assertFalse(comm.exists())
