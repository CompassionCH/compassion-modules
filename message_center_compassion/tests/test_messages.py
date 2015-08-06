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

from openerp.tests import common
from openerp.osv import orm
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config

from datetime import date
from random import randint
import logging
logger = logging.getLogger(__name__)


class test_messages(common.TransactionCase):
    """Test and simulate reception of GMC Messages.
    Warning : Please make sure module sponsorship_sync_gp is not installed
              in order to be sure no information is sent to GP.
    """

    def setUp(self):
        super(test_messages, self).setUp()
        self.message_obj = self.registry('gmc.message.pool')
        self.action_obj = self.registry('gmc.action')
        self.child_obj = self.registry('compassion.child')
        self.today = date.today().strftime(DF)
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'receivable'),
            ])[0]
        property_account_receivable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'receivable'),
                ('user_type', '=', account_type)
            ])[0]
        account_type = self.registry('account.account.type').search(
            self.cr, self.uid, [
                ('code', '=', 'payable'),
            ])[0]
        property_account_payable = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'payable'),
                ('user_type', '=', account_type)])[0]
        self.property_account_income = self.registry('account.account').search(
            self.cr, self.uid, [
                ('type', '=', 'other'),
                ('name', '=', 'Property Account Income Test')
            ])[0]
        category_id = self.registry('res.partner.category').create(
            self.cr, self.uid, {
                'name': 'sponsor',
            })
        self.partner_id = self.registry('res.partner').create(
            self.cr, self.uid, {
                'lang': 'fr_CH',
                'lastname': 'Client 37',
                'property_account_receivable': property_account_receivable,
                'property_account_payable': property_account_payable,
                'notification_email_send': 'none',
                'category_id': [(4, category_id)],
            })
        self.payment_term_id = self.registry('account.payment.term').search(
            self.cr, self.uid, [
                ('name', '=', '15 Days')
            ])[0]
        self.origin_id = self.registry('recurring.contract.origin').create(
            self.cr, self.uid, {
                'name': 'other',
                'type': 'event',
            })
        self.group_id = self._create_group_id(
            'do_nothing', 1, 'month', self.partner_id, 1, self.payment_term_id)

    def _allocate_new_children(self, child_keys):
        """Creates allocate message and process them for given
        child keys.
        """
        if not isinstance(child_keys, list):
            child_keys = [child_keys]
        context = {'test_mode': True}
        message_ids = [self._create_allocate_message(child_key)
                       for child_key in child_keys]
        self.message_obj.process_messages(self.cr, self.uid, message_ids,
                                          context)
        return self.child_obj.search(self.cr, self.uid,
                                     [('code', 'in', child_keys)])

    def _create_allocate_message(self, child_key, child_id=0):
        """Creates an allocate message. If child_id is given, the allocation
        is on an existing child."""
        action_id = self.action_obj.search(self.cr, self.uid, [
            ('type', '=', 'allocate'), ('model', '=', 'compassion.child')])[0]
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
        return self.message_obj.create(self.cr, self.uid, message_vals)

    def _create_incoming_message(self, type, model, object_id, child_key='',
                                 event=''):
        """Generic method for creating an incoming message and process it.
        Args:
            - type: one of ('update','deallocate','depart')
            - model: either 'compassion.child' or 'compassion.project'
            - object_id: id of related child or project object
        """
        context = {'test_mode': True}
        action_id = self.action_obj.search(self.cr, self.uid, [
            ('type', '=', type), ('model', '=', model)])[0]
        message_vals = {
            'date': self.today,
            'action_id': action_id,
            'object_id': object_id,
            'incoming_key': child_key,
            'partner_country_code': 'CH',
            'event': event
        }
        mess_id = self.message_obj.create(self.cr, self.uid, message_vals)
        self.message_obj.process_messages(self.cr, self.uid, [mess_id],
                                          context)
        return mess_id

    def _create_active_contract(self, child_id):
        """Creates a new contract for given child."""
        contract_vals = {
            'partner_id': self.partner_id,
            'correspondant_id': self.partner_id,
            'origin_id': self.origin_id,
            'group_id': self.group_id,
            'channel': 'direct',
            'num_pol_ga': randint(700, 999),
            'child_id': child_id,
            'next_invoice_date': self.today,
            'activation_date': self.today,
            'type': 'S',
        }
        con_obj = self.registry('recurring.contract')
        con_id = con_obj.create(
            self.cr, self.uid, contract_vals, context={'default_type': 'S'})
        con_obj.force_activation(self.cr, self.uid, con_id)
        return con_id

    def _send_messages(self, message_type, failure_reason='', will_fail=False):
        """Looks for existing outgoing messages of given message_type
        and process (send) them. Simulate reception of a confirmation
        message from GMC which can be success or failure."""
        context = {'test_mode': True}
        mess_ids = self.message_obj.search(self.cr, self.uid, [
            ('direction', '=', 'out'), ('name', '=', message_type),
            ('state', '=', 'new')])
        self.assertTrue(mess_ids)
        if will_fail:
            with self.assertRaises(orm.except_orm):
                self.message_obj.process_messages(self.cr, self.uid, mess_ids,
                                                  context)
        else:
            self.message_obj.process_messages(self.cr, self.uid, mess_ids,
                                              context)
            status = 'success' if not failure_reason else 'failure'
            if message_type == 'CreateGift' and status == 'success':
                # Gifts messages go to 'fondue' status.
                status = 'fondue'
            for message in self.message_obj.browse(self.cr, self.uid,
                                                   mess_ids):
                    # Messages must be pending
                    self.assertEqual(message.state, 'pending')
                    self.assertTrue(message.request_id)
                    self.message_obj.ack(self.cr, self.uid, message.request_id,
                                         status, failure_reason)
            for message in self.message_obj.browse(self.cr, self.uid,
                                                   mess_ids):
                # Messages must have a valid status
                self.assertEqual(message.state, status)

        return mess_ids

    def _create_gift(self, contract_id):
        """Creates a Gift Invoice for given contract using the
        Generate Gift Wizard of module sponsorship_compassion
        """
        gift_id = self.registry('product.product').search(
            self.cr, self.uid, [('name', '=', 'Project Gift')])[0]
        self.registry('product.product').write(
            self.cr, self.uid, gift_id, {
                'property_account_income': self.property_account_income,
            })
        gift_wizard = self.registry('generate.gift.wizard')
        wizard_id = gift_wizard.create(
            self.cr, self.uid, {
                'amount': 60,
                'product_id': gift_id,
                'invoice_date': self.today,
                'description': 'gift for bicycle'
            })
        res = gift_wizard.generate_invoice(self.cr, self.uid, [wizard_id],
                                           {'active_ids': [contract_id]})
        inv_ids = res['domain'][0][2]
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'account.invoice', inv_ids[0], 'invoice_open', self.cr)
        self._pay_invoice(inv_ids[0])

    def _create_group_id(self, change_method, rec_value, rec_unit, partner_id,
                         adv_biling_months, payment_term_id, ref=None):
        """
            Create a group with 2 possibilities :
                - ref is not given so it takes "/" default values
                - ref is given
        """
        group_obj = self.registry('recurring.contract.group')
        group_id = group_obj.create(self.cr, self.uid, {
            'partner_id': partner_id,
        })
        group = group_obj.browse(self.cr, self.uid, group_id)
        group_vals = {
            'change_method': change_method,
            'recurring_value': rec_value,
            'recurring_unit': rec_unit,
            'partner_id': partner_id,
            'advance_billing_months': adv_biling_months,
            'payment_term_id': payment_term_id,
        }
        if ref:
            group_vals['ref'] = ref
        group.write(group_vals)
        return group_id

    def test_config_set(self):
        """Test that the config is properly set on the server.
        """
        url = config.get('middleware_url')
        self.assertTrue(url)

    def test_gmc_scenario(self):
        """This is the test scenario detailed in file
        ..data/test_scenario.docx
        """
        context = {'test_mode': True}
        # Simulate GMC Allocation of 4 new children
        child_keys = ["PE3760148", "IO6790210"]  # , "UG8320012", "UG8350016"]
        child_ids = self._allocate_new_children(child_keys)
        # Check all 4 children are available in database
        self.assertEqual(len(child_ids), len(child_keys))
        for child in self.child_obj.browse(self.cr, self.uid, child_ids):
            self.assertEqual(child.state, 'N')
            self.assertFalse(child.has_been_sponsored)
            self.assertTrue(child.name)
            self.assertTrue(child.case_study_ids)
            self.assertTrue(child.unique_id)

        # Create a commitment for one child
        con_id = self._create_active_contract(child_ids[0])

        ######################################################################
        #               Test child departure and reinstatement               #
        ######################################################################
        child_departed_id = child_ids[0]
        self._send_messages('UpsertConstituent')
        self._send_messages('CreateCommitment')
        self._create_incoming_message(
            'depart', 'compassion.child', child_departed_id)
        child = self.child_obj.browse(self.cr, self.uid, child_departed_id)
        self.assertEqual(child.state, 'F')
        self._send_messages('CancelCommitment')

        # The child reinstated should be in the correct state
        mess_id = self._create_allocate_message(
            child_keys[0], child_departed_id)
        self.message_obj.process_messages(self.cr, self.uid, [mess_id],
                                          context)
        child = self.child_obj.browse(self.cr, self.uid, child_departed_id)
        self.assertEqual(child.state, 'Z')

        # The sponsorship should be terminated
        contract_obj = self.registry('recurring.contract')
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(contract.state, 'terminated')
        self.assertEqual(contract.gmc_state, 'depart')
        self.assertEqual(contract.end_reason, '1')  # child departure

        # Test child deallocation
        self._create_incoming_message(
            'deallocate', 'compassion.child', child_departed_id)
        child = self.child_obj.browse(self.cr, self.uid, child_departed_id)
        self.assertEqual(child.state, 'X')

        ######################################################################
        # Test transfer scenario (update message with new child_key)         #
        # for a sponsored child.                                             #
        # we simulate a different key by manually writing another code       #
        ######################################################################
        con_id = self._create_active_contract(child_ids[1])
        self._create_incoming_message(
            'update', 'compassion.child', child_ids[1], 'UG8360007',
            'Transfer')
        child = self.child_obj.browse(self.cr, self.uid, child_ids[1])
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(contract.state, 'active')
        self.assertEqual(child.state, 'P')
        self.assertEqual(child.code, 'UG8360007')
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
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(contract.gmc_state, 'casestudy')
        self._create_incoming_message(
            'update', 'compassion.child', child_ids[1], child_keys[1],
            'NewImage')
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(contract.gmc_state, 'picture')

        project_id = self.registry('compassion.project').search(
            self.cr, self.uid, [('code', '=', child_keys[1][:5])])[0]
        self._create_incoming_message(
            'update', 'compassion.project', project_id)

        # Test sending gifts
        self._create_gift(con_id)
        # Send gift before commitment
        self._send_messages('CreateGift', will_fail=True)
        # Send Constituent and Commitment
        self._send_messages('UpsertConstituent')
        self._send_messages('CreateCommitment')
        # Send Gift
        self._send_messages('CreateGift')

        # Sponsor cancels the sponsorship
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(self.uid, 'recurring.contract', con_id,
                                'contract_terminated', self.cr)
        self._send_messages('CancelCommitment')

    def _pay_invoice(self, invoice_id):
        journal_obj = self.registry('account.journal')
        bank_journal_id = self.registry('account.journal').search(
            self.cr, self.uid, [('type', '=', 'bank')])[0]
        bank_journal = journal_obj.browse(self.cr, self.uid, bank_journal_id)
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoice_id)
        account_id = invoice.partner_id.property_account_receivable.id
        move_obj = self.registry('account.move')
        move_line_obj = self.registry('account.move.line')
        move_id = move_obj.create(self.cr, self.uid, {
            'journal_id': bank_journal_id
        })
        move_line_obj.create(self.cr, self.uid, {
            'name': 'BNK-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': bank_journal.default_debit_account_id.id,
            'debit': invoice.amount_total,
            'journal_id': bank_journal_id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        mv_line_id = move_line_obj.create(self.cr, self.uid, {
            'name': 'PAY-' + invoice.number,
            'move_id': move_id,
            'partner_id': invoice.partner_id.id,
            'account_id': account_id,
            'credit': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_due
        })
        move_obj.button_validate(self.cr, self.uid, [move_id])
        to_reconcile = move_line_obj.search(self.cr, self.uid, [
            ('move_id', '=', invoice.move_id.id),
            ('account_id', '=', account_id)]) + [mv_line_id]
        move_line_obj.reconcile(self.cr, self.uid, to_reconcile)
