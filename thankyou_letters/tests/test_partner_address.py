##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from markupsafe import Markup

from odoo.tests import TransactionCase


class TestPartnerAddress(TransactionCase):
    """The address of a contact carries markup and has to keep it.

    A letter and an e-mail both write the address with a t-out. When the
    address is a plain string, the line breaks it holds are escaped and the
    reader sees the tags printed in the middle of the address.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.title = cls.env["res.partner.title"].search(
            [("shortcut", "!=", False)], limit=1
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "firstname": "Camille",
                "lastname": "Rochat",
                "title": cls.title.id,
                "street": "Rue Galilée 3",
                "zip": "1400",
                "city": "Yverdon-les-Bains",
                "country_id": cls.env.ref("base.ch").id,
                "lang": "en_US",
            }
        )

    def _render(self, source):
        """Write the address the way a letter or an e-mail template does."""
        return self.env["ir.qweb"]._render(
            self.env["ir.ui.view"]
            .sudo()
            .create(
                {
                    "name": "address rendering",
                    "type": "qweb",
                    "arch": f'<t><span t-out="{source}"/></t>',
                }
            )
            .id,
            {"partner": self.partner},
        )

    def test_short_address_keeps_its_line_breaks(self):
        self.assertIsInstance(self.partner.short_address, Markup)
        rendered = self._render("partner.short_address")
        self.assertIn("Rue Galilée 3<br/>", rendered)
        self.assertNotIn("&lt;br/&gt;", rendered)

    def test_address_without_name_drops_only_the_name(self):
        address = self.partner.address_without_name
        self.assertIsInstance(address, Markup)
        self.assertNotIn(self.partner.lastname, address)
        self.assertIn("Rue Galilée 3", address)
        self.assertIn("Yverdon-les-Bains", address)
        rendered = self._render("partner.address_without_name")
        self.assertNotIn("&lt;br/&gt;", rendered)

    def test_address_without_name_of_a_contact_that_has_no_title(self):
        """Without a name line to drop, the whole address has to stay."""
        self.partner.title = False
        self.assertIn("Rue Galilée 3", self.partner.address_without_name)
