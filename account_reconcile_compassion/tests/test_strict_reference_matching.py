from odoo.tests import TransactionCase


class TestStrictReferenceMatching(TransactionCase):
    def setUp(self):
        pass

    def test_apply_rules_strict_reference_matching(self):
        rec_models = self.env["account.reconcile.model"].search([])
        st_lines = []
        reconciliations = rec_models._apply_rules(self, st_lines, excluded_ids=None, partner_map=None)
