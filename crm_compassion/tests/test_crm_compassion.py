# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
logger = logging.getLogger(__name__)


class test_crm_compassion(common.TransactionCase):

    def setUp(self):
        super(test_crm_compassion, self).setUp()
        # Creation of partners
        self.admin_id = self.env['res.users'].search(
            [('name', '=', 'Administrator')])[0].id
        self.partner_id = self.env['res.partner'].search(
            [('name', '=', 'Michel Fletcher')])[0].id

    def test_crm_compassion(self):
        """
            This scenario consists in the creation of an opportunity,
            then comes the event. Check if the project which is created from
            the event has coherent data with the event.
            Check if we can find the origin from the event in a sponsorship
            contract.
        """

        # Creation of a lead and an event
        lead = self._create_lead(
            'PlayoffsCompassion', self.admin_id)
        lead2 = self._create_lead(
            'JO_Compassion', self.admin_id)
        self.assertTrue(lead.id)
        event = self._create_event(lead)
        event2 = self._create_event(lead2)
        self.assertTrue(event.id)
        event.write({'use_tasks': True, 'partner_id': self.partners[2].id})
        event2.write({'use_tasks': True, 'partner_id': self.partners[2].id})
        self.assertTrue(event.project_id)

        # Retrieve of the project from the event
        project = self.env['project.project'].browse(event.project_id.id)

        # Creation of a marketing project and check if an origin is created
        self._create_project(
            'Marketing Project', 'employees', self.admin_id, 'marketing', True)
        mark_origin = self.env['recurring.contract.origin'].search(
            [('type', '=', 'marketing')])
        self.assertTrue(mark_origin)
        self.assertEqual(project.date_start, event.start_date[:10])
        self.assertEqual(project.analytic_account_id, event.analytic_id)
        self.assertEqual(project.project_type, event.type)
        self.assertEqual(project.user_id, event.user_id)
        self.assertEqual(project.name, event.name)

        # Create a child and get the project associated
        child = self._create_child('PE3760136')
        child.project_id.write({'disburse_funds': True})

        # Creation of the sponsorship contract
        sp_group = self._create_group(
            'do_nothing', self.partners[2], 1, self.payment_term_id)
        sponsorship = self._create_sponsorship(
            datetime.today().strftime(DF), sp_group,
            datetime.today().strftime(DF),
            other_vals={
                'origin_id': event.origin_id.id
                'channel': 'postal',
                'type': 'S',
                'child_id': child.id,
                'correspondant_id': sp_group.partner_id.id
            })
        sponsorship.write({'user_id': self.partner_id})
        self.assertEqual(sponsorship.origin_id.name, event.full_name)
        self.assertEqual(sponsorship.state, 'draft')
        sponsorship.signal_workflow('contract_validated'))
        invoicer_obj = self.env['recurring.invoicer']
        invoicer_id = sponsorship.button_generate_invoices()
        invoices = invoicer_obj.browse(invoicer_id).invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(
            invoices[0].invoice_line[0].user_id, sponsorship.user_id)
        event_dico = self.partners[2].open_events()
        self.assertEqual(len(event_dico['domain'][0][2]), 2)

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

    def _create_event(self, lead):
        event_dico = lead.create_event(context={})
        event = self.env['crm.event.compassion'].create(
            {
                'name': event_dico['context']['default_name'],
                'type': 'sport',
                'start_date': datetime.today().strftime(DF),
                'lead_id': lead.id,
                'user_id': event_dico['context']['default_user_id'],
                'parent_id': 7,
            })
        return event

    def _create_lead(self, name, user_id):
        lead = self.env['crm.lead'].create(
            {
                'name': name,
                'user_id': user_id,
            })
        return lead
