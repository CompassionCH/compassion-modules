##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime

from odoo import _, fields

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)


class TestAccountReconcile(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

        self.t_child = self.create_child("TT123456789")
        self.t_partner = self.env["res.users"].search([("company_id", "=", 1)], limit=1)
        t_group = self.create_group({"partner_id": self.t_partner.id})
        self.t_sponsorship = self.create_contract(
            {
                "partner_id": self.t_partner.id,
                "group_id": t_group.id,
                "child_id": self.t_child.id,
            },
            [{"amount": 50.0}],
        )
        self.company = self.env["res.company"].search([("id", "=", 1)], limit=1)
        self.journal = self.env["account.journal"].search([("code", "=", "CCP")])
        self.account = self.env["account.account"].search(
            [("id", "=", self.journal.default_credit_account_id.id)]
        )
        self.account.write({"currency_id": self.env.ref("base.CHF").id})

    def test_account_reconcile(self):
        self.assertTrue(self.journal)
        self.assertTrue(self.company)
        self.assertTrue(self.account)

        move = self.env["account.move"].create(
            {
                "name": "test_acc_move",
                "date": fields.Date.today(),
                "journal_id": self.journal.id,
                "state": "draft",
                "company_id": self.company.id,
                "ref": "test_ref",
            }
        )
        self.assertTrue(move)

        date_maturity = str(datetime.datetime(datetime.datetime.today().year, 12, 12))
        account_move_line = self.env["account.move.line"].create(
            {
                "name": "test_move_line",
                "account_id": self.account.id,
                "move_id": move.id,
                "date_maturity": date_maturity,
                "currency_id": self.env.ref("base.CHF").id,
            }
        )
        self.assertTrue(account_move_line)

        account_move_line_today = self.env["account.move.line"].create(
            {
                "name": "test_move_line",
                "account_id": self.account.id,
                "move_id": move.id,
                "date_maturity": fields.Date.today(),
                "currency_id": self.env.ref("base.CHF").id,
            }
        )
        self.assertTrue(account_move_line_today)

        bank_statement = self.env["account.bank.statement"].create(
            {
                "date": fields.Date.today(),
                "state": "open",
                "journal_id": self.journal.id,
                "move_line_ids": [
                    (6, _, [account_move_line.id, account_move_line_today.id])
                ],
            }
        )
        self.assertTrue(bank_statement)

        bank_statement_line = self.env["account.bank.statement.line"].create(
            {
                "name": "TestBankLine",
                "date": fields.Date.today(),
                "amount": 50,
                "journal_id": self.journal.id,
                "account_id": self.account.id,
                "statement_id": bank_statement.id,
                "ref": "test_ref",
                "currency_id": self.env.ref("base.GBP").id,
                "journal_entry_ids": [(6, _, move.line_ids.ids)],
            }
        )
        self.assertTrue(bank_statement_line)

        # test linking partner to bank when writing to
        # account.bank.statement.line
        self.env["account.bank.statement.line"].write({"partner_id": self.t_partner.id})
        partner_bank = self.env["res.partner.bank"].search(
            [
                "|",
                ("acc_number", "like", self.journal.bank_account_id.acc_number),
                (
                    "sanitized_acc_number",
                    "like",
                    self.journal.bank_account_id.acc_number,
                ),
            ]
        )
        self.assertEqual(partner_bank.company_id, self.journal.company_id)

        acc_partial_rec = self.env["account.partial.reconcile"].create(
            {
                "debit_move_id": account_move_line.id,
                "credit_move_id": account_move_line.id,
            }
        )
        self.assertTrue(acc_partial_rec)
