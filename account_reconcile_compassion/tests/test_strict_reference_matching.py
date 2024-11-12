import unittest

from odoo.tests import TransactionCase

EMPTY_RECONCILIATION = {"aml_ids": []}


class TestStrictReferenceMatching(TransactionCase):
    def _create_unpaid_invoice_line(self, payment_reference: str):
        unpaid_invoice = self.env["account.move"].create(
            {
                "journal_id": 1,
                "partner_id": self.partner1.id,
                "payment_state": "not_paid",
                # Different from ref for absl1 to test strict vs unstrict reconciliation
                "payment_reference": payment_reference,
                "company_id": 1,
            }
        )
        return self.env["account.move.line"].create(
            {"move_id": unpaid_invoice.id, "account_id": self.invoice_account.id}
        )

    def _create_absl(self, payment_reference: str):
        bank_statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.journal.id,
            }
        )
        return self.env["account.bank.statement.line"].create(
            {
                "name": "Test bank statement line",
                "statement_id": bank_statement.id,
                "payment_ref": payment_reference,
                "amount": 100.0,
                "to_check": True,
                "company_id": 1,
            }
        )

    def setUp(self):
        super(TestStrictReferenceMatching, self).setUp()

        account_reconcile_model = self.env["account.reconcile.model"]
        self.invoice_matching_rule_strict = account_reconcile_model.create(
            {
                "rule_type": "invoice_matching",
                "strict_reference_matching": True,
                "name": "Test strict invoice mathing rule",
            }
        )

        self.invoice_matching_rule_unstrict = account_reconcile_model.create(
            {
                "rule_type": "invoice_matching",
                "strict_reference_matching": False,
                "name": "Test unstrict invoice mathing rule",
            }
        )

        counterpart_account = self.env["account.account"].create(
            {
                "name": "Test counterpart account",
                "code": "1",
                "user_type_id": 1,
                "reconcile": True,
            }
        )
        self.invoice_account = self.env["account.account"].create(
            {
                "name": "Test invoice account",
                "code": "2",
                "user_type_id": 1,
                "reconcile": True,
            }
        )
        account_type = self.env["account.account.type"].create(
            {"name": "Test", "type": "other", "internal_group": "income"}
        )
        default_account = self.env["account.account"].create(
            {
                "name": "Default account",
                "code": "3",
                "user_type_id": account_type.id,
                "reconcile": True,
            }
        )

        self.journal = self.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "001",
                "type": "sale",
                "suspense_account_id": counterpart_account.id,
                "default_account_id": default_account.id,
            }
        )

        payment_ref_1 = "001"
        payment_ref_2 = "002"

        self.partner1 = self.env["res.partner"].create({"name": "Test partner"})
        self.absl1 = self._create_absl(payment_ref_1)
        self.absl2 = self._create_absl(payment_ref_2)

        # Used in call to _apply_rules
        self.partner_map = {self.absl1.id: self.partner1.id}

        self.st_lines = self.absl1

        self.unpaid_invoice_line1 = self._create_unpaid_invoice_line(payment_ref_1)
        self.unpaid_invoice_line2 = self._create_unpaid_invoice_line(payment_ref_2)

    @unittest.skip(
        """Some unknown setup/context issue prevents the reconciliation from
                   working"""
    )
    def test_apply_rules_unstrict_reference_matching(self):
        reconciliations = self.invoice_matching_rule_unstrict._apply_rules(
            self.st_lines, partner_map=self.partner_map
        )
        self.assertEqual(len(reconciliations), 1)
        self.assertIn(self.absl1.id, reconciliations)
        self.assertIn("partner_id", reconciliations[self.absl1.id])

    def test_apply_rules_strict_reference_matching(self):
        reconciliations = self.invoice_matching_rule_strict._apply_rules(
            self.st_lines, partner_map=self.partner_map
        )
        self.assertEqual(len(reconciliations), 1)
        self.assertIn(self.absl1.id, reconciliations)

        # The strict reconciliation should have prevented the approximate reconciliation
        self.assertNotIn("partner_id", reconciliations[self.absl1.id])

    def _build_reconciliations(self, rec_model) -> dict:
        return {
            812: EMPTY_RECONCILIATION,
            810: EMPTY_RECONCILIATION,
            self.absl1.id: {
                "model": rec_model,
                "aml_ids": [self.unpaid_invoice_line2.id],  # Incorrect reconciliation
                "partner": self.partner1,
            },
            self.absl2.id: {
                "model": rec_model,
                "aml_ids": [self.unpaid_invoice_line2.id],  # Correct reconciliation
                "partner": self.partner1,
            },
        }

    def test_filter_reconciliations_strict_ref(self):
        reconciliations = self._build_reconciliations(self.invoice_matching_rule_strict)
        filtered_reconciliations = self.env[
            "account.reconcile.model"
        ]._filter_reconciliations_strict_ref(reconciliations, self.st_lines)

        # Reconciliation filter should not change the number of reconciliation objects
        self.assertEqual(len(reconciliations), len(filtered_reconciliations))

        # Strict reconciliation should have removed the incorrect reconciliation
        self.assertEqual(filtered_reconciliations[self.absl1.id], EMPTY_RECONCILIATION)
        self.assertEqual(
            filtered_reconciliations[self.absl2.id], reconciliations[self.absl2.id]
        )

    def test_filter_reconciliations_unstrict_ref(self):
        reconciliations = self._build_reconciliations(
            self.invoice_matching_rule_unstrict
        )
        filtered_reconciliations = self.env[
            "account.reconcile.model"
        ]._filter_reconciliations_strict_ref(reconciliations, self.st_lines)

        # Reconciliation filter should not change the number of reconciliation objects
        self.assertEqual(len(reconciliations), len(filtered_reconciliations))

        # Unstrict reconciliation should have kept the approximate reconciliation
        self.assertEqual(
            filtered_reconciliations[self.absl1.id], reconciliations[self.absl1.id]
        )
        self.assertEqual(
            filtered_reconciliations[self.absl2.id], reconciliations[self.absl2.id]
        )
