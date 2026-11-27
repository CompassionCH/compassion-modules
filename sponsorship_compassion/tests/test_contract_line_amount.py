##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from .test_contract_compassion import BaseContractCompassionTest


class TestContractLineAmount(BaseContractCompassionTest):
    """The invoiced amount of a contract line: the pricelist price for the
    sponsorship product, the line amount for any other product."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product = cls.env["product.product"]
        cls.sponsorship_product = product.create(
            {
                "name": "Sponsorship price test",
                "categ_id": cls.env.ref(
                    "sponsorship_compassion.product_category_sponsorship"
                ).id,
            }
        )
        cls.fund_product = product.create(
            {
                "name": "Fund price test",
                "categ_id": cls.env.ref(
                    "sponsorship_compassion.product_category_fund"
                ).id,
            }
        )
        cls.pricelist_item = {}
        for prod, price in ((cls.sponsorship_product, 42), (cls.fund_product, 50)):
            cls.pricelist_item[prod] = cls.env["product.pricelist.item"].create(
                {
                    "pricelist_id": cls.pricelist.id,
                    "applied_on": "1_product",
                    "product_tmpl_id": prod.product_tmpl_id.id,
                    "compute_price": "fixed",
                    "fixed_price": price,
                }
            )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Donor price test", "country_id": cls.env.ref("base.ch").id}
        )

    def _contract(self, product, amount):
        return self.create_contract(
            {
                "partner_id": self.partner.id,
                "group_id": self.create_group({"partner_id": self.partner.id}).id,
            },
            [{"product_id": product.id, "amount": amount}],
        )

    def _invoiced_price(self, contract):
        contract.contract_waiting()
        lines = self.env["account.move.line"].search(
            [("contract_id", "=", contract.id), ("product_id", "!=", False)]
        )
        self.assertTrue(lines, "the contract generated no invoice")
        self.assertEqual(set(lines.mapped("price_unit")), {lines[0].price_unit})
        return lines[0].price_unit

    def test_invoice_takes_the_line_amount_of_a_priced_product(self):
        contract = self._contract(self.fund_product, 42)
        self.assertFalse(contract.contract_line_ids.amount_from_pricelist)
        self.assertEqual(self._invoiced_price(contract), 42)

    def test_invoice_takes_the_pricelist_price_of_the_sponsorship(self):
        contract = self._contract(self.sponsorship_product, 30)
        self.assertTrue(contract.contract_line_ids.amount_from_pricelist)
        self.assertEqual(self._invoiced_price(contract), 42)

    def test_price_update_reaches_only_sponsorship_lines(self):
        sponsorship = self._contract(self.sponsorship_product, 42)
        donation = self._contract(self.fund_product, 42)
        for prod in (self.sponsorship_product, self.fund_product):
            item = self.pricelist_item[prod]
            item.fixed_price = 45
            item.update_cl_amount()
        self.assertEqual(sponsorship.contract_line_ids.amount, 45)
        self.assertEqual(donation.contract_line_ids.amount, 42)
