# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.exceptions import Warning
from openerp.addons.contract_compassion.tests.test_base_module\
    import test_base_module
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config

from datetime import date
from random import randint
import logging
logger = logging.getLogger(__name__)


class test_messages(test_base_module):
    """Test and simulate reception of GMC Messages.
    Warning : Please make sure module sponsorship_sync_gp is not installed
              in order to be sure no information is sent to GP.
    """

    def setUp(self):
        super(test_messages, self).setUp()
        self.message_obj = self.env['gmc.message.pool'].with_context(
            async_mode=False, test_mode=True)
        self.action_obj = self.env['gmc.action']
        self.child_obj = self.env['compassion.child']
        self.today = date.today().strftime(DF)
        self.origin = self.env['recurring.contract.origin'].create(
            {
                'name': 'other',
                'type': 'event'
            })
        self.group = self._create_group(
            'do_nothing', self.partners.ids[0], 1,
            self.payment_term_id,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})

    def _allocate_new_children(self, child_keys):
        """Creates allocate message and process them for given
        child keys.
        """
        if not isinstance(child_keys, list):
            child_keys = [child_keys]
        messages = self.message_obj
        for child_key in child_keys:
            messages |= self._create_allocate_message(child_key)
        messages.process_messages()
        return self.child_obj.search([('code', 'in', child_keys)])

    def _create_allocate_message(self, child_key, child_id=0):
        """Creates an allocate message. If child_id is given, the allocation
        is on an existing child."""
        action_id = self.action_obj.search([
            ('type', '=', 'allocate'),
            ('model', '=', 'compassion.child')])[0].id
        message_vals = {
            'date': self.today,
            'action_id': action_id,
            'incoming_key': child_key,
            'partner_country_code': 'CH'
        }
        if child_id:
            message_vals.update({
                'child_id': child_id,
                'object_id': child_id
            })
        return self.message_obj.create(message_vals)

    def _create_incoming_message(self, type, model, object_id, child_key='',
                                 event=''):
        """Generic method for creating an incoming message and process it.
        Args:
            - type: one of ('update','deallocate','depart')
            - model: either 'compassion.child' or 'compassion.project'
            - object_id: id of related child or project object
        """
        action_id = self.action_obj.search([
            ('type', '=', type), ('model', '=', model)])[0].id
        message_vals = {
            'date': self.today,
            'action_id': action_id,
            'object_id': object_id,
            'incoming_key': child_key,
            'partner_country_code': 'CH',
            'event': event
        }
        mess = self.message_obj.create(message_vals)
        mess.process_messages()
        return mess

    def _create_active_contract(self, child_id):
        """Creates a new contract for given child."""
        contract_vals = {
            'partner_id': self.partners.ids[0],
            'correspondant_id': self.partners.ids[0],
            'origin_id': self.origin.id,
            'group_id': self.group.id,
            'channel': 'direct',
            'num_pol_ga': randint(700, 999),
            'child_id': child_id,
            'next_invoice_date': self.today,
            'type': 'S',
        }
        con_obj = self.env['recurring.contract'].with_context(
            default_type='S', async_mode=False)
        contract = con_obj.create(contract_vals)
        contract.force_activation()
        return contract

    def _send_messages(self, message_type, failure_reason='', will_fail=False):
        """Looks for existing outgoing messages of given message_type
        and process (send) them. Simulate reception of a confirmation
        message from GMC which can be success or failure."""
        messages = self.message_obj.search([
            ('direction', '=', 'out'), ('name', '=', message_type),
            ('state', '=', 'new')])
        self.assertTrue(messages)
        if will_fail:
            with self.assertRaises(Warning):
                messages.process_messages()
            for message in messages:
                self.assertEqual(message.state, 'failure')
            messages.write({'state': 'new'})
        else:
            messages.process_messages()
            status = 'success' if not failure_reason else 'failure'
            if message_type == 'CreateGift' and status == 'success':
                # Gifts messages go to 'fondue' status.
                status = 'fondue'
            for message in messages:
                # Messages must be pending
                self.assertEqual(message.state, 'pending')
                self.assertTrue(message.request_id)

            self.message_obj.ack(message.request_id, status, failure_reason)
            for message in messages:
                # Messages must have a valid status
                self.assertEqual(message.state, status)

        return messages

    def _create_gift(self, contract_id):
        """Creates a Gift Invoice for given contract using the
        Generate Gift Wizard of module sponsorship_compassion
        """
        gift = self.env['product.product'].search([
            ('name', '=', 'Project Gift')])[0]
        gift.write({
            'property_account_income': self.property_account_income})
        gift_wizard = self.env['generate.gift.wizard'].with_context(
            active_ids=[contract_id])
        wizard = gift_wizard.create({
            'amount': 60,
            'product_id': gift.id,
            'invoice_date': self.today,
            'description': 'gift for bicycle'})
        res = wizard.generate_invoice()
        inv_ids = res['domain'][0][2]
        invoices = self.env['account.invoice'].browse(inv_ids)
        invoices[0].signal_workflow('invoice_open')
        self._pay_invoice(invoices[0])

    def test_config_set(self):
        """Test that the config is properly set on the server.
        """
        url = config.get('middleware_url')
        self.assertTrue(url)

    def test_gmc_scenario(self):
        """This is the test scenario detailed in file
        ..data/test_scenario.docx
        """
        # Simulate GMC Allocation of 4 new children
        child_keys = ["PE3760148", "IO6790210"]  # , "UG8320012", "UG8350016"]
        children = self._allocate_new_children(child_keys)
        child_ids = children.ids
        # Check all 4 children are available in database
        self.assertEqual(len(children), len(child_keys))
        for child in children:
            self.assertEqual(child.state, 'N')
            self.assertFalse(child.has_been_sponsored)
            self.assertTrue(child.name)
            self.assertTrue(child.case_study_ids)
            self.assertTrue(child.global_id)

        # Create a commitment for one child
        contract = self._create_active_contract(child_ids[0])

        ######################################################################
        #               Test child departure and reinstatement               #
        ######################################################################
        child_departed_id = child_ids[0]
        self._send_messages('UpsertConstituent')
        self._send_messages('CreateCommitment')
        self._create_incoming_message(
            'depart', 'compassion.child', child_departed_id)
        child = children[0]
        self.assertEqual(child.state, 'F')
        self._send_messages('CancelCommitment')

        # The child reinstated should be in the correct state
        message = self._create_allocate_message(
            child_keys[0], child_departed_id)
        message.process_messages()
        self.assertEqual(child.state, 'Z')

        # The sponsorship should be terminated
        self.assertEqual(contract.state, 'terminated')
        self.assertEqual(contract.gmc_state, 'depart')
        self.assertEqual(contract.end_reason, '1')  # child departure

        # Test child deallocation
        self._create_incoming_message(
            'deallocate', 'compassion.child', child_departed_id)
        self.assertEqual(child.state, 'X')

        ######################################################################
        # Test transfer scenario (update message with new child_key)         #
        # for a sponsored child.                                             #
        # we simulate a different key by manually writing another code       #
        ######################################################################
        contract = self._create_active_contract(child_ids[1])
        self._create_incoming_message(
            'update', 'compassion.child', child_ids[1], 'UG08360007',
            'Transfer')
        child = children[1]
        self.assertEqual(contract.state, 'active')
        self.assertEqual(child.state, 'P')
        self.assertEqual(child.local_id, 'UG08360007')
        self.assertEqual(child.sponsor_id.id, contract.partner_id.id)
        self.assertEqual(contract.state, 'active')
        self.assertEqual(contract.gmc_state, 'transfer')
        self.assertEqual(contract.child_id.id, child.id)

        ######################################################################
        #            Test UpdateChild and UpdateProject messages             #
        #           We only need to check that no error is raised            #
        ######################################################################
        self._create_incoming_message(
            'update', 'compassion.child', child_ids[1], child_keys[1],
            'CaseStudy')
        self.assertEqual(contract.gmc_state, 'casestudy')
        self._create_incoming_message(
            'update', 'compassion.child', child_ids[1], child_keys[1],
            'NewImage')
        self.assertEqual(contract.gmc_state, 'picture')

        project_id = self.env['compassion.project'].search(
            [('code', '=', child_keys[1][:5])])[0].id
        self._create_incoming_message(
            'update', 'compassion.project', project_id)

        # Test sending gifts
        self._create_gift(contract.id)
        # Send gift before commitment
        self._send_messages('CreateGift', will_fail=True)
        # Send Constituent and Commitment
        self._send_messages('UpsertConstituent')
        self._send_messages('CreateCommitment')
        # Send Gift
        self._send_messages('CreateGift')

        # Sponsor cancels the sponsorship
        contract.signal_workflow('contract_terminated')
        self._send_messages('CancelCommitment')
