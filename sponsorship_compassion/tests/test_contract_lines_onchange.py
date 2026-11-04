##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import Form, TransactionCase


def ensure_standard_products(env):
    """The products of the standard sponsorship lines: demo data of this
    module, data of the countries' modules. They must exist once."""
    for code in ("sponsorship", "fund_gen"):
        if not env["product.template"].search_count([("default_code", "=", code)]):
            env["product.product"].create(
                {"name": f"{code} test", "default_code": code}
            )


class TestContractLinesOnchange(TransactionCase):
    """The standard lines of a child sponsorship, set again when its payment
    options are chosen in the form."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ensure_standard_products(cls.env)
        cls.partner_1 = cls.env["res.partner"].create({"name": "Sponsor Lines"})
        cls.sp_group = cls.env["recurring.contract.group"].create(
            {"partner_id": cls.partner_1.id}
        )

    def _new_contract(self, contract_type):
        form = Form(
            self.env["recurring.contract"].with_context(default_type=contract_type)
        )
        form.type = contract_type
        form.partner_id = self.partner_1
        while len(form.contract_line_ids):
            form.contract_line_ids.remove(0)
        return form

    def _products(self, form):
        product_ids = [line["product_id"] for line in form.contract_line_ids._records]
        return self.env["product.product"].browse(product_ids).mapped("default_code")

    def test_a_sponsorship_gets_its_lines_with_its_payment_options(self):
        form = self._new_contract("S")
        form.group_id = self.sp_group
        self.assertIn("sponsorship", self._products(form))

    def test_a_write_and_pray_gets_its_lines_with_its_payment_options(self):
        form = self._new_contract("SWP")
        form.group_id = self.sp_group
        self.assertIn("sponsorship", self._products(form))
