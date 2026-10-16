##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOriginCampaign(TransactionCase):
    """A sponsorship takes the campaign of its origin, unless it has its own."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Origin campaign sponsor", "country_id": cls.env.ref("base.ch").id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Origin campaign donation", "type": "service", "list_price": 40}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Origin campaign pricelist"}
        )
        cls.group = cls.env["recurring.contract.group"].create(
            {
                "partner_id": cls.partner.id,
                "advance_billing_months": 1,
                "recurring_value": 1,
                "recurring_unit": "month",
            }
        )
        campaign_obj = cls.env["utm.campaign"]
        cls.magazine = campaign_obj.create({"title": "Origin campaign magazine"})
        cls.newspaper = campaign_obj.create({"title": "Origin campaign newspaper"})
        cls.own = campaign_obj.create({"title": "Origin campaign own"})
        cls.unknown = cls.env.ref("sponsorship_compassion.utm_source_unknown")
        origin_obj = cls.env["recurring.contract.origin"]
        cls.origin_magazine = origin_obj.create(
            {
                "type": "other",
                "other_name": "Origin campaign A",
                "campaign_id": cls.magazine.id,
            }
        )
        cls.origin_newspaper = origin_obj.create(
            {
                "type": "other",
                "other_name": "Origin campaign B",
                "campaign_id": cls.newspaper.id,
            }
        )
        cls.origin_none = origin_obj.create(
            {"type": "other", "other_name": "Origin campaign C"}
        )

    def _contract(self, **vals):
        return self.env["recurring.contract"].create(
            {
                "type": "O",
                "partner_id": self.partner.id,
                "group_id": self.group.id,
                "pricelist_id": self.pricelist.id,
                "contract_line_ids": [
                    (0, 0, {"product_id": self.product.id, "amount": 40.0})
                ],
                **vals,
            }
        )

    def test_create_takes_origin_campaign(self):
        contract = self._contract(origin_id=self.origin_magazine.id)
        self.assertEqual(contract.campaign_id, self.magazine)

    def test_create_keeps_own_campaign(self):
        contract = self._contract(
            origin_id=self.origin_magazine.id, campaign_id=self.own.id
        )
        self.assertEqual(contract.campaign_id, self.own)

    def test_change_of_origin(self):
        follower = self._contract(origin_id=self.origin_magazine.id)
        without = self._contract()
        own = self._contract(origin_id=self.origin_magazine.id, campaign_id=self.own.id)
        (follower | without | own).write({"origin_id": self.origin_newspaper.id})
        self.assertEqual(follower.campaign_id, self.newspaper)
        self.assertEqual(without.campaign_id, self.newspaper)
        self.assertEqual(own.campaign_id, self.own)
        # The campaign of the previous origin doesn't stay on the sponsorship
        follower.origin_id = self.origin_none
        self.assertFalse(follower.campaign_id)

    def test_change_of_origin_campaign(self):
        follower = self._contract(origin_id=self.origin_none.id)
        own = self._contract(origin_id=self.origin_none.id, campaign_id=self.own.id)
        self.origin_none.campaign_id = self.magazine
        self.assertEqual(follower.campaign_id, self.magazine)
        self.assertEqual(own.campaign_id, self.own)
        self.origin_none.campaign_id = self.newspaper
        self.assertEqual(follower.campaign_id, self.newspaper)
        self.assertEqual(own.campaign_id, self.own)

    def test_source_follows_origin(self):
        magazine = self.env["utm.source"].create({"name": "Origin campaign magazine"})
        own = self.env["utm.source"].create({"name": "Origin campaign own"})
        follower = self._contract(origin_id=self.origin_none.id)
        kept = self._contract(origin_id=self.origin_none.id, source_id=own.id)
        self.origin_none.source_id = magazine
        self.assertEqual(follower.source_id, magazine)
        self.assertEqual(kept.source_id, own)
        follower.origin_id = self.origin_magazine
        self.assertEqual(follower.source_id, self.unknown)
        self.assertEqual(follower.campaign_id, self.magazine)

    def test_unknown_source(self):
        contract = self._contract(origin_id=self.origin_none.id)
        self.assertEqual(contract.source_id, self.unknown)
        # An unknown source follows the origin as an empty one
        magazine = self.env["utm.source"].create({"name": "Origin campaign print"})
        self.origin_none.source_id = magazine
        self.assertEqual(contract.source_id, magazine)
