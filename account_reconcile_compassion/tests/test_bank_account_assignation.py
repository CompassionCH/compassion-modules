##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields
from odoo.tests import TransactionCase


class TestAccountReconcile(TransactionCase):
    """
    This will test the assignation of res.partner.bank when a bank statement
    line contains a bank acccount information and we assign it to a partner.
    """

    def setUp(self):
        super().setUp()
        self.asustek = self.env.ref("base.res_partner_1")
        self.camptocamp = self.env.ref("base.res_partner_12")
        journal = self.env.ref("l10n_ch_pain_direct_debit.dd_account_journal_xml_dd")
        self.statement = self.env["account.bank.statement"].create(
            {
                "journal_id": journal.id,
                "date": fields.Date.today(),
            }
        )

    def test_assign_partner_bank(self):
        """
        Create a new partner_bank and test when bank.statement.line is
        assigned to partner, the partner_bank is also assigned to the partner
        """
        acc_number = "77777777"
        bank_account = self.env["res.partner.bank"].create(
            {"partner_id": self.asustek.id, "acc_number": acc_number}
        )
        line = self.env["account.bank.statement.line"].create(
            {
                "statement_id": self.statement.id,
                "name": "test bank assignation",
                "date": fields.Date.today(),
                "amount": 10,
                "partner_account": acc_number,
            }
        )
        line.partner_id = self.asustek
        self.assertEqual(bank_account.partner_id, self.asustek)

        # Subsequent assignation should not change the partner of the bank
        line = self.env["account.bank.statement.line"].create(
            {
                "statement_id": self.statement.id,
                "name": "test new bank assignation",
                "date": fields.Date.today(),
                "amount": 120,
                "partner_account": acc_number,
            }
        )
        line.partner_id = self.camptocamp
        self.assertEqual(bank_account.partner_id, self.asustek)
