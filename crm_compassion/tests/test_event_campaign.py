##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEventCampaign(TransactionCase):
    """An event is a source, or a campaign for peer-to-peer fundraising, given
    to its origin and to its sponsorships."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Event campaign sponsor", "country_id": cls.env.ref("base.ch").id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Event campaign donation", "type": "service", "list_price": 40}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Event campaign pricelist"}
        )
        cls.group = cls.env["recurring.contract.group"].create(
            {
                "partner_id": cls.partner.id,
                "advance_billing_months": 1,
                "recurring_value": 1,
                "recurring_unit": "month",
            }
        )

    def _event(self, **vals):
        now = datetime.now()
        return self.env["crm.event.compassion"].create(
            {
                "name": "Campaign test concert",
                "type": "concert",
                "start_date": now,
                "end_date": now + timedelta(days=1),
                "hold_start_date": now.date(),
                "user_id": self.env.uid,
                **vals,
            }
        )

    def _contract(self, origin, **vals):
        return self.env["recurring.contract"].create(
            {
                "type": "O",
                "partner_id": self.partner.id,
                "group_id": self.group.id,
                "pricelist_id": self.pricelist.id,
                "origin_id": origin.id,
                "contract_line_ids": [
                    (0, 0, {"product_id": self.product.id, "amount": 40.0})
                ],
                **vals,
            }
        )

    def test_event_is_a_source(self):
        event = self._event()
        self.assertEqual(event.source_id.name, event.full_name)
        self.assertFalse(event.campaign_id)
        self.assertEqual(event.origin_id.source_id, event.source_id)
        contract = self._contract(event.origin_id)
        self.assertEqual(contract.source_id, event.source_id)

    def test_peer_to_peer_event_is_a_campaign(self):
        event = self._event(type="sport", name="Campaign test run")
        self.assertEqual(event.campaign_id.title, event.full_name)
        self.assertFalse(event.source_id)
        self.assertEqual(event.origin_id.campaign_id, event.campaign_id)

    def test_event_keeps_given_campaign(self):
        tour = self.env["utm.campaign"].create({"title": "Campaign test tour"})
        event = self._event(campaign_id=tour.id)
        self.assertEqual(event.campaign_id, tour)
        self.assertEqual(event.origin_id.campaign_id, tour)
        self.assertEqual(self._contract(event.origin_id).campaign_id, tour)

    def test_change_of_event_campaign(self):
        event = self._event()
        follower = self._contract(event.origin_id)
        own_campaign = self.env["utm.campaign"].create({"title": "Campaign test own"})
        own = self._contract(event.origin_id, campaign_id=own_campaign.id)
        tour = self.env["utm.campaign"].create({"title": "Campaign test tour"})
        event.campaign_id = tour
        self.assertEqual(event.origin_id.campaign_id, tour)
        self.assertEqual(follower.campaign_id, tour)
        self.assertEqual(own.campaign_id, own_campaign)

    def test_utm_follows_event_name(self):
        event = self._event()
        event.name = "Campaign test gospel concert"
        self.assertEqual(event.source_id.name, event.full_name)
        # A source named otherwise keeps its name
        event.source_id.name = "Campaign test gospel night"
        event.name = "Campaign test gospel evening"
        self.assertEqual(event.source_id.name, "Campaign test gospel night")
        run = self._event(type="sport", name="Campaign test run")
        run.name = "Campaign test relay"
        self.assertEqual(run.campaign_id.title, run.full_name)

    def test_copy_gets_own_source(self):
        event = self._event()
        copy = event.copy()
        self.assertTrue(copy.source_id)
        self.assertNotEqual(copy.source_id, event.source_id)
