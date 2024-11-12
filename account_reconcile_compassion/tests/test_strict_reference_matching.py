import unittest
from odoo.tests import TransactionCase


EMPTY_RECONCILIATION = {"aml_ids": []}


class TestStrictReferenceMatching(TransactionCase):
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
        invoice_account = self.env["account.account"].create(
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

        journal = self.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "001",
                "type": "sale",
                "suspense_account_id": counterpart_account.id,
                "default_account_id": default_account.id,
            }
        )
        abs = self.env["account.bank.statement"]
        abs1 = abs.create(
            {
                "journal_id": journal.id,
            }
        )

        absl = self.env["account.bank.statement.line"]

        payment_ref_1 = "001"
        payment_ref_2 = "002"

        self.partner1 = self.env["res.partner"].create({"name": "Test partner"})
        self.absl1 = absl.create(
            {
                "name": "Test bank statement line",
                "statement_id": abs1.id,
                "payment_ref": payment_ref_1,
                "amount": 100.0,
                "to_check": True,
                "company_id": 1,
            }
        )
        absl.flush()

        # Used in call to _apply_rules
        self.partner_map = {self.absl1.id: self.partner1.id}

        self.st_lines = self.absl1

        unpaid_invoice2 = self.env["account.move"].create(
            {
                "journal_id": 1,
                "partner_id": self.partner1.id,
                "payment_state": "not_paid",
                # Different from ref for absl1 to test strict vs unstrict reconciliation
                "payment_reference": payment_ref_2,
                "company_id": 1,
            }
        )
        self.unpaid_invoice_line2 = self.env["account.move.line"].create(
            {"move_id": unpaid_invoice2.id, "account_id": invoice_account.id}
        )
        unpaid_invoice2.action_post()

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
