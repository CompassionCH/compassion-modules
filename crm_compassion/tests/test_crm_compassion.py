##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, timedelta

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

logger = logging.getLogger(__name__)


class TestCrmCompassion(BaseSponsorshipTest):
    def test_crm(self):
        """
            This scenario consists in the creation of an opportunity,
            then comes the event.
            Check if we can find the origin from the event in a sponsorship
            contract.
        """
        # Creation of a lead and an event
        lead = self._create_lead("PlayoffsCompassion", 1)
        lead2 = self._create_lead("JO_Compassion", 1)
        self.assertTrue(lead.id)
        event = self._create_event(lead, "sport")
        event2 = self._create_event(lead2, "sport")
        self.assertTrue(event.id)
        event.write({"use_tasks": True, "partner_id": self.david.id})
        event2.write({"use_tasks": True, "partner_id": self.david.id})

        # Creation of the sponsorship contract
        child = self.create_child("AB123456789")
        sp_group = self.create_group({"partner_id": self.thomas.id})
        sponsorship = self.create_contract(
            {
                "partner_id": self.thomas.id,
                "group_id": sp_group.id,
                "origin_id": event.origin_id.id,
                "child_id": child.id,
                "correspondent_id": sp_group.partner_id.id,
            },
            [{"amount": 50.0}],
        )
        sponsorship.write({"user_id": self.michel.id})
        mark_origin = self.env["recurring.contract.origin"].search(
            [("type", "=", "marketing")]
        )
        self.assertEqual(sponsorship.origin_id.name, event.full_name)
        self.assertEqual(sponsorship.state, "draft")
        sponsorship.write({"origin_id": mark_origin.id})
        sponsorship.on_change_origin()
        self.validate_sponsorship(sponsorship)
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_id.invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, "open")
        self.assertEqual(invoices[0].invoice_line_ids[0].user_id, sponsorship.user_id)
        event_dico = self.david.open_events()
        self.assertEqual(len(event_dico["domain"][0][2]), 2)
        is_unlinked = event.unlink()
        self.assertTrue(is_unlinked)

    def test_calendar_event_synchronization(self):
        lead = self._create_lead("MyLead", 1)

        event = self._create_event(lead, "sport")
        self.assertEqual(event.calendar_event_id.duration, 9)

        in_two_days = datetime.today().date() + timedelta(days=2)
        event.end_date = datetime.combine(in_two_days, datetime.min.time())
        self.assertEqual(event.calendar_event_id.duration, 48)

        # The event duration should have a lower bound of 3 hours
        event.end_date = datetime.combine(datetime.today(), datetime.min.time())
        self.assertEqual(event.calendar_event_id.duration, 3)

    def _create_event(self, lead, event_type):
        event_dico = lead.create_event()
        now = datetime.today().date()
        event = self.env["crm.event.compassion"].create(
            {
                "name": event_dico["context"]["default_name"],
                "type": event_type,
                "start_date": now,
                "end_date": datetime.today().replace(hour=8, minute=43),
                "hold_start_date": now,
                "hold_end_date": now,
                "number_allocate_children": 2,
                "planned_sponsorships": 0,
                "lead_id": lead.id,
                "user_id": event_dico["context"]["default_user_id"],
            }
        )
        return event

    def _create_lead(self, name, user_id):
        lead = self.env["crm.lead"].create({"name": name, "user_id": user_id, })
        return lead
