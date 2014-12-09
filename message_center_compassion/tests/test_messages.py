# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
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

    def _allocate_new_children(self, child_keys):
        """Creates allocate message and process them for given
        child keys.
        """
        message_ids = [self._create_allocate_message(child_key)
                       for child_key in child_keys]
        self.message_obj.process_messages(self.cr, self.uid, message_ids)
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
            'incoming_key': child_key
        }
        if child_id:
            message_vals.update({
                'child_id': child_id,
                'object_id': child_id
            })
        return self.message_obj.create(self.cr, self.uid, message_vals)

    def _create_incoming_message(self, type, model, object_id):
        """Generic method for creating an incoming message and process it.
        Args:
            - type: one of ('update','deallocate',depart')
            - model: either 'compassion.child' or 'compassion.project'
            - object_id: id of related child or project object
        """
        action_id = self.action_obj.search(self.cr, self.uid, [
            ('type', '=', type), ('model', '=', model)])[0]
        message_vals = {
            'date': self.today,
            'action_id': action_id,
            'object_id': object_id
        }
        mess_id = self.message_obj.create(self.cr, self.uid, message_vals)
        self.message_obj.process_messages(self.cr, self.uid, [mess_id])
        return mess_id
        
    def _create_active_contract(self, child_id):
        """Creates a new contract and activate it for given child."""
        sponsor_category = self.registry('res.partner.category').search(
            self.cr, self.uid, [('name', 'ilike', 'sponsor')])
        partner_ids = self.registry('res.partner').search(
            self.cr, self.uid, [('category_id', 'in', sponsor_category)])
        origin_ids = self.registry('recurring.contract.origin').search(
            self.cr, self.uid, [('name', 'like', 'Other')])
        contract_vals = {
            'partner_id': partner_ids[0],
            'correspondant_id': partner_ids[0],
            'origin_id': origin_ids[0],
            'channel': 'direct',
            'child_id': child_id
        }
        con_obj = self.registry('recurring.contract')
        con_id = con_obj.create(self.cr, self.uid, contract_vals)
        con_obj.activate_from_gp(self.cr, self.uid, con_id)
        return con_id
        
    def _send_messages(self, message_type, failure_reason='', will_fail=False):
        """Looks for existing outgoing messages of given message_type
        and process (send) them. Simulate reception of a confirmation
        message from GMC which can be success or failure."""
        mess_ids = self.message_obj.search(self.cr, self.uid, [
            ('direction', '=', 'out'), ('name', '=', message_type)])
        self.assertTrue(mess_ids)
        if will_fail:
            with self.assertRaises(orm.except_orm):
                self.message_obj.process_messages(self.cr, self.uid, mess_ids)
        else:
            self.message_obj.process_messages(self.cr, self.uid, mess_ids)
            status = 'success' if not failure_reason else 'failure'
            for message in self.message_obj.browse(self.cr, self.uid, mess_ids):
                # Messages must be pending and have a valid request_id
                self.assertEqual(message.state, 'pending')
                self.assertTrue(message.request_id)
                self.message_obj.ack(message.request_id, status, failure_reason)
            for message in self.message_obj.browse(self.cr, self.uid, mess_ids):
                # Messages must have a valid status
                self.assertEqual(message.state, status)

        return mess_ids
        
    def _create_gift(self, contract_id):
        """Creates a Gift Invoice for given contract using the
        Generate Gift Wizard of module sponsorship_compassion
        """
        gift_id = self.registry('product.product').search(
            self.cr, self.uid, [('name', '=', 'Birthday Gift')])[0]
        gift_wizard = self.registry('generate.gift.wizard')
        wizard_id = gift_wizard.create(
            self.cr, self.uid, {
                'amount': 60,
                'product_id': gift_id,
                'invoice_date': self.today,
                'description': 'gift for bicycle'
            })
        res = gift_wizard.generate_invoice(self.cr, self.uid, [wizard_id],
                                     {'active_id': contract_id})
        inv_id = res['res_id']
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            uid, 'account.invoice', inv_id, 'invoice_open', cr)
        self._pay_invoice(inv_id)
        

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
        child_keys = ["PE3760148", "IN6890248", "ID6000122", "ID6000139"]
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

        # Test sending gifts before commitment is sent to GMC
        self._create_gift(con_id)
        self._send_messages('CreateGift',
                            failure_reason='Unknown Constituent',
                            will_fail=True)
        
        # Test sending commitment to GMC
        self._send_messages('CreateCommitment')

        # Test child departure and reinstatement
        # TODO: When GetExitDetails will be working, test this
        #       scenario on sponsored child. For now, we test it
        #       on an available child for simplicity.
        child_departed_id = child_ids[1]
        self._create_incoming_message('depart', 'compassion.child', child_departed_id)
        # For now the action does not automatically mark the child as departed.
        self.child_obj.write(self.cr, self.uid, {'state': 'F'})

        # The child is reinstated and should again be available
        self._create_allocate_message(child_keys[1], child_departed_id)
        child = self.child_obj.browse(self.cr, self.uid, child_departed_id)
        self.assertEqual(child.state, 'N')

        # Test child deallocation
        self._create_incoming_message('deallocate', 'compassion.child', child_departed_id)
        child = self.child_obj.browse(self.cr, self.uid, child_departed_id)
        self.assertEqual(child.state, 'X')
        
        # Test transfer scenario (deallocate -> allocate with new child_key)
        # for a sponsored child.
        # we simulate a different key by manually writing another code
        self._create_incoming_message('deallocate', 'compassion.child', child_ids[0])
        child = self.child_obj.browse(self.cr, self.uid, child_ids[0])
        contract_obj = self.registry('recurring.contract')
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(contract.state, 'active')
        self.assertEqual(child.state, 'X')

        self._create_incoming_message('allocate', 'compassion.child', child_ids[0])
        child.write({'code': 'TT1234567'})
        child = self.child_obj.browse(self.cr, self.uid, child_ids[0])
        contract = contract_obj.browse(self.cr, self.uid, con_id)
        self.assertEqual(child.state, 'P')
        self.assertEqual(child.sponsor_id, True)
        self.assertEqual(contract.state, 'active')
        self.assertEqual(contract.child_id.id, child.id)

        # Test UpdateChild and UpdateProject messages
        # We only need to check that no error is raised
        self._create_incoming_message('update', 'compassion.child', 'ID6000122')
        self._create_incoming_message('update', 'compassion.project', 'ID600')

        # Test sending gifts
        self._send_messages('CreateGift')

        # Sponsor cancels the sponsorship
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            uid, 'recurring.contract', con_id, 'contract_terminated', cr)
        self._send_messages('CancelCommitment')
        
    def _pay_invoice(self, invoice_id):
        journal_obj = self.registry('account.journal')
        bank_journal_id = self.registry('account.journal').search(
            self.cr, self.uid, [('type', '=', 'bank')])[0]
        bank_journal = journal_obj.browse(self.cr, self.uid, bank_journal_id)
        account_id = self.registry('account.account').search(
            self.cr, self.uid, [('code', '=', '1050')])[0]
        move_obj = self.registry('account.move')
        move_line_obj = self.registry('account.move.line')
        invoice = self.registry('account.invoice').browse(
            self.cr, self.uid, invoice_id)
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
