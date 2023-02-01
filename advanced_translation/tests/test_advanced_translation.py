from odoo.tests.common import SingleTransactionCase


class AdvancedTranslationTest(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        """ Create test data."""
        super().setUpClass()

        cls.test_partner_obj = cls.env["res.partner"]
        tang = cls.browse_ref(cls, "base.res_partner_address_1")
        joseph = cls.browse_ref(cls, "base.res_partner_address_2")
        cls.males = (tang + joseph).with_context(lang="en_US")
        julia = cls.browse_ref(cls, "base.res_partner_address_33")
        jessica = cls.browse_ref(cls, "base.res_partner_address_14")
        (julia + jessica).write({"gender": "F"})
        cls.females = (julia + jessica).with_context(lang="en_US")

    def test_keyword_gender(self):
        """Testing that the correct term is returned given the recordset.
        """
        self.assertEqual(self.males[:1].get("demo_his"), "his")
        self.assertEqual(self.males.get("demo_his"), "their(m)")
        self.assertEqual(self.females[:1].get("demo_his"), "her")
        self.assertEqual(self.females.get("demo_his"), "their(f)")

    def test_missing_keyword(self):
        """Missing keyword should return the translation of the term."""
        self.assertEqual(self.males.get("Hello"), "Hello")

    def test_get_list(self):
        """Should return comma separated values."""
        self.assertEqual(
            self.males.sorted("name").get_list("name"), "Ron Gibson and Willie Burke"
        )
        self.assertEqual(self.males.get_list("name", 1, "test"), "test")
        self.assertEqual(self.males.get_list("gender"), "Male")
        self.assertEqual(
            (self.males + self.females).sorted("gender").get_list("gender"),
            "Female and Male",
        )
