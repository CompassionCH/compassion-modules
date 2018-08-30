# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from datetime import datetime, timedelta
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
logger = logging.getLogger(__name__)


class TestCrmCompassion(BaseSponsorshipTest):

    def test_crm(self):
        """
            This scenario consists in the creation of an opportunity,
            then comes the event. Check if the project which is created from
            the event has coherent data with the event.
            Check if we can find the origin from the event in a sponsorship
            contract.
        """
        # Creation of a lead and an event
        lead = self._create_lead(
            'PlayoffsCompassion', 1)
        lead2 = self._create_lead(
            'JO_Compassion', 1)
        self.assertTrue(lead.id)
        event = self._create_event(lead, 'sport')
        event2 = self._create_event(lead2, 'sport')
        self.assertTrue(event.id)
        event.write({'use_tasks': True, 'partner_id': self.david.id})
        event2.write({'use_tasks': True, 'partner_id': self.david.id})
        self.assertTrue(event.project_id)

        # Retrieve of the project from the event
        project = self.env['project.project'].browse(event.project_id.id)

        # Creation of a marketing project and check if an origin is created
        self._create_project(
            'Marketing Project', 'employees', 1, 'marketing', True)
        mark_origin = self.env['recurring.contract.origin'].search(
            [('type', '=', 'marketing')])
        self.assertTrue(mark_origin)
        self.assertEqual(project.date_start, event.start_date[:10])
        self.assertEqual(project.analytic_account_id, event.analytic_id)
        self.assertEqual(project.project_type, event.type)
        self.assertEqual(project.user_id, event.user_id)
        self.assertEqual(project.name, event.name)
        # Create a child and get the project associated
        child = self.create_child('AB123456789')

        # Creation of the sponsorship contract
        sp_group = self.create_group({'partner_id': self.thomas.id})
        sponsorship = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': sp_group.id,
                'origin_id': event.origin_id.id,
                'child_id': child.id,
                'correspondent_id': sp_group.partner_id.id
            },
            [{'amount': 50.0}]
        )
        sponsorship.write({'user_id': self.michel.id})
        self.assertEqual(sponsorship.origin_id.name, event.full_name)
        self.assertEqual(sponsorship.state, 'draft')
        sponsorship.write({'origin_id': mark_origin.id})
        sponsorship.on_change_origin()
        self.validate_sponsorship(sponsorship)
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_id.invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(
            invoices[0].invoice_line_ids[0].user_id, sponsorship.user_id)
        event_dico = self.david.open_events()
        self.assertEqual(len(event_dico['domain'][0][2]), 2)
        is_unlinked = event.unlink()
        self.assertTrue(is_unlinked)

    def test_calendar_event_synchronization(self):
        lead = self._create_lead('MyLead', 1)

        event = self._create_event(lead, 'sport')
        self.assertEqual(event.calendar_event_id.duration, 9)

        in_two_days = (datetime.today() + timedelta(days=2)).strftime(DF)
        event.write({
            'end_date': in_two_days,
        })
        self.assertEqual(event.calendar_event_id.duration, 48)

        # The event duration should have a lower bound of 3 hours
        event.write({
            'end_date': datetime.today().strftime(DF),
        })
        self.assertEqual(event.calendar_event_id.duration, 3)

    def _create_project(self, name, privacy_visibility, user_id, type, bool):
        project_id = self.env['project.project'].create(
            {
                'name': name,
                'privacy_visibility': privacy_visibility,
                'user_id': user_id,
                'project_type': type,
                'use_tasks': bool,
                'date_start': datetime.today().strftime(DF),
            })
        return project_id

    def _create_event(self, lead, type):
        event_dico = lead.create_event()
        now = datetime.today().strftime(DF)
        event = self.env['crm.event.compassion'].create(
            {
                'name': event_dico['context']['default_name'],
                'type': type,
                'start_date': now,
                'end_date': now + ' 8:43:00',
                'hold_start_date': now,
                'hold_end_date': now,
                'number_allocate_children': 2,
                'planned_sponsorships': 0,
                'lead_id': lead.id,
                'user_id': event_dico['context']['default_user_id'],
            })
        return event

    def _create_lead(self, name, user_id):
        lead = self.env['crm.lead'].create(
            {
                'name': name,
                'user_id': user_id,
            })
        return lead
