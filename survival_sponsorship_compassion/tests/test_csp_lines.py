##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import Form, TransactionCase


class TestCspLines(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create({"name": "CSP Sponsor"})
        cls.sp_group = cls.env["recurring.contract.group"].create(
            {"partner_id": cls.partner_1.id}
        )

    def test_a_csp_keeps_its_country_with_its_payment_options(self):
        """Staff choose the country of a survival sponsorship, then its payment
        options: the country's line stays (it was replaced by the child
        sponsorship's, the type CSP containing an "S")."""
        country = self.env["product.product"].create(
            {"name": "Survival Sponsorship Test Country", "list_price": 62}
        )
        form = Form(self.env["recurring.contract"].with_context(default_type="S"))
        form.type = "CSP"
        form.partner_id = self.partner_1
        while len(form.contract_line_ids):
            form.contract_line_ids.remove(0)
        with form.contract_line_ids.new() as line:
            line.product_id = country
        form.group_id = self.sp_group
        product_ids = [line["product_id"] for line in form.contract_line_ids._records]
        self.assertEqual(product_ids, country.ids)
