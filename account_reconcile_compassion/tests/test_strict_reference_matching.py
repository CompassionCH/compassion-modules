from odoo.tests import TransactionCase


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
        

        abs = self.env["account.bank.statement"]
        abs1 = abs.create(
            {
                "journal_id": 1,
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
        absl = self.env["account.bank.statement.line"]

        payment_ref_1 = "001"
        payment_ref_2 = "002"

        absl1 = absl.create(
            {
                "statement_id": abs1.id,
                "payment_ref": payment_ref_1,
                "counterpart_account_id": counterpart_account.id,
            }
        )
        absl.flush()

        partner1 = self.env["res.partner"].create({"name": "Test partner"})

        self.partner_map = {
            absl1.id: partner1.id
        }

        self.st_lines = absl.search([])

        unpaid_invoice1 = self.env["account.move"].create(
            {
                "journal_id": 1,
                "partner_id": partner1.id,
                "payment_state": "not_paid",
                # Different from ref for absl1 to test strict vs unstrict reconciliation
                "payment_reference": payment_ref_2, 
            }
        )
        invoice_line_1 = self.env["account.move.line"].create(
            {"move_id": unpaid_invoice1.id, "account_id": invoice_account.id}
        )

    def test_apply_rules_unstrict_reference_matching(self):
        reconciliations = self.invoice_matching_rule_unstrict._apply_rules(self.st_lines, partner_map=self.partner_map)
        # TODO should find match
        pass

    def test_apply_rules_strict_reference_matching(self):
        reconciliations = self.invoice_matching_rule_strict._apply_rules(self.st_lines, partner_map=self.partner_map)
        # TODO should not find match
        pass
