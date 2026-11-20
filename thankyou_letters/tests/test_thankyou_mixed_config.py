##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestThankYouMixedConfig(AccountTestInvoicingCommon):
    """A donation can ask for a specific thank you (e.g. Christmas). When an
    invoice holds donations asking for different thank you letters (e.g. a
    MyCompassion basket), the standard thank you is used for all of them.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["thankyou.config"].create(
            {"min_donation_amount": 0, "send_mode": "auto_digital_only"}
        )
        cls.standard_config = cls.env.ref("thankyou_letters.config_thankyou_standard")
        cls.christmas_config = cls.standard_config.copy()
        cls.campaign_config = cls.standard_config.copy()
        cls.gift = cls._create_donation_product("Child gift")
        cls.christmas = cls._create_donation_product(
            "Christmas Gift", cls.christmas_config
        )
        cls.campaign = cls._create_donation_product("Campaign", cls.campaign_config)

    @classmethod
    def _create_donation_product(cls, name, config=None):
        return cls.env["product.product"].create(
            {
                "name": name,
                "lst_price": 50,
                "requires_thankyou": True,
                "partner_communication_config": config.id if config else False,
            }
        )

    def _thank(self, *products):
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, products=products, post=True
        )
        comm_ids = invoice.invoice_line_ids.generate_thank_you()
        return self.env["partner.communication.job"].browse(comm_ids)

    def test_specific_donations_get_their_thank_you(self):
        comm = self._thank(self.christmas, self.christmas)
        self.assertEqual(comm.config_id, self.christmas_config)

    def test_specific_with_standard_donation_gets_standard_thank_you(self):
        comm = self._thank(self.gift, self.christmas)
        self.assertEqual(comm.config_id, self.standard_config)
        self.assertEqual(len(comm.get_objects()), 2)

    def test_two_specific_donations_get_standard_thank_you(self):
        comm = self._thank(self.christmas, self.campaign)
        self.assertEqual(comm.config_id, self.standard_config)
        self.assertEqual(len(comm.get_objects()), 2)
