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

from openerp import netsvc
from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.config import config

from datetime import datetime, date

from ..model import gp_connector
import logging

logger = logging.getLogger(__name__)


class test_contracts(common.TransactionCase):

    """ Test Contracts Synchronization with GP """

    def setUp(self):
        super(test_contracts, self).setUp()
        self.gp_connect = gp_connector.GPConnect(self.cr, self.uid)

    def _create_contract_for_cino(self, child_id):
        """ Creates a new contract for partner Emanuel Cino """
        cino_id = self.registry('res.partner').search(
            self.cr, self.uid, [('name', 'like', 'Cino Emanuel')])
        con_obj = self.registry('recurring.contract')
        cino_con_id = con_obj.search(self.cr, self.uid,
                                     [('partner_id', 'in', cino_id)])
        self.assertTrue(cino_con_id)
        origin_ids = self.registry('recurring.contract.origin').search(
            self.cr, self.uid, [('name', 'like', 'Other')])
        default = {
            'origin_id': origin_ids[0],
            'channel': 'direct'
        }
        self.assertTrue(
            con_obj.copy(self.cr, self.uid, cino_con_id[0], default=default))
        res_ids = con_obj.search(
            self.cr, self.uid,
            [('partner_id', 'in', cino_id), ('state', '=', 'draft')])
        self.assertTrue(res_ids)
        con_obj.write(self.cr, self.uid, res_ids, {
            'child_id': child_id})
        return res_ids[0]

    def test_config_set(self):
        """Test that the config is properly set on the server
        """
        host = config.get('mysql_host')
        user = config.get('mysql_user')
        pw = config.get('mysql_pw')
        db = config.get('mysql_db')
        self.assertTrue(host)
        self.assertTrue(user)
        self.assertTrue(pw)
        self.assertTrue(db)
        self.assertTrue(self.gp_connect.is_alive())

    def test_contract_lifecycle(self):
        """Test a whole lifecycle of contract and verifies
        synchronization with GP.
        """
        contract_obj = self.registry('recurring.contract')
        wf_service = netsvc.LocalService('workflow')
        con_id = 0
        child_id = 0
        old_child_state = ''
        try:
            # Find an available child
            child_obj = self.registry('compassion.child')
            child_ids = child_obj.search(self.cr, self.uid,
                                         [('state', 'in', ('N', 'R'))])
            self.assertTrue(child_ids)
            child_id = child_ids[0]
            old_child_state = child_obj.browse(
                self.cr, self.uid, child_id).state

            # Test that the state of the child is the same in GP and Odoo
            child_state_sql = "SELECT Situation FROM Enfants WHERE id_erp = %s"
            gp_state = self.gp_connect.selectOne(
                child_state_sql, child_id).get("Situation")
            self.assertEqual(old_child_state, gp_state)

            # Create new contract
            con_id = self._create_contract_for_cino(child_id)

            # Test that the child is marked as sponsored in GP and Odoo
            child = child_obj.browse(self.cr, self.uid, child_id)
            child_state = child.state
            self.assertEqual(child_state, 'P')
            gp_state = self.gp_connect.selectOne(
                child_state_sql, child_id).get("Situation")
            self.assertEqual(gp_state, 'P')

            # Various checks on child object
            self.assertTrue(child.sponsor_id)
            self.assertTrue(child.has_been_sponsored)

            # Check that GP is synced with information of contract.
            contract = contract_obj.browse(self.cr, self.uid, con_id)
            self.assertEqual(contract.state, 'draft')
            self._check_contract_sync(contract, 'C', 0)

            # Validate contract and test synchronization
            contract_obj.validate_from_gp(self.cr, self.uid, con_id)
            contract = contract_obj.browse(self.cr, self.uid, con_id)
            self.assertEqual(contract.state, 'waiting')
            next_invoice_date = datetime.strptime(contract.next_invoice_date,
                                                  DF).date()
            month_paid = next_invoice_date.month
            today = date.today()
            if next_invoice_date.day <= 15:
                month_paid -= 1
            if month_paid == 0 and today.month == 12:
                month_paid = 12
            self._check_contract_sync(contract, 'C', month_paid)

            # Generate invoice and make payment, then test synchronization
            invoice_ids = self._generate_invoices(contract.group_id)
            self._pay_invoices(invoice_ids)
            contract = contract_obj.browse(self.cr, self.uid, con_id)
            self.assertEqual(contract.state, 'active')
            month_paid += len(invoice_ids)
            self._check_contract_sync(contract, 'S', month_paid)

            # Terminate contract and test state
            # End reason : sponsor not satisfied
            # Note : we could also check a child depart
            contract.write({'end_reason': '5'})
            wf_service.trg_validate(
                self.uid, 'recurring.contract', contract.id,
                'contract_terminated', self.cr)
            contract = contract_obj.browse(self.cr, self.uid, con_id)
            self._check_contract_sync(contract, 'F', month_paid)
            self.assertEqual(contract.state, 'terminated')

            # Various checks on child after end of sponsorship
            child = child_obj.browse(self.cr, self.uid, child_id)
            self.assertEqual(child.state, 'R')  # child waits a new sponsor
            gp_state = self.gp_connect.selectOne(
                child_state_sql, child_id).get("Situation")
            self.assertEqual(gp_state, 'R')
            self.assertTrue(child.has_been_sponsored)
            self.assertFalse(child.sponsor_id)

        finally:
            # End of test, clean GP from the changes
            if con_id:
                self.gp_connect.query(
                    'Update Enfants SET Situation=%s, CODEGA=NULL '
                    'WHERE id_erp = %s', [old_child_state, child_id])
                self.gp_connect.query('DELETE FROM Poles WHERE id_erp = %s',
                                      con_id)
            del(self.gp_connect)

    def _check_contract_sync(self, contract, state, month_paid):
        gp_contract = self.gp_connect.selectOne(
            "SELECT * From Poles WHERE id_erp=%s", contract.id)
        self.assertTrue(gp_contract)
        sponsor_ref = contract.child_id.sponsor_id.ref
        if state == 'F':
            sponsor_ref = contract.partner_id.ref
        self.assertEqual(gp_contract.get('CODEGA'), sponsor_ref)
        self.assertEqual(gp_contract.get('TYPEP'), state)
        self.assertEqual(
            gp_contract.get('TYPEVERS'), self.gp_connect._find_typevers(
                contract.group_id.payment_term_id.name, 'OP'))
        self.assertEqual(gp_contract.get('BASE'), contract.total_amount)
        self.assertEqual(
            gp_contract.get('FREQPAYE'),
            self.gp_connect.freq_mapping[contract.group_id.advance_billing])
        self.assertEqual(gp_contract.get('MOIS'), month_paid)

    def _generate_invoices(self, contract_group):
        invoicer_obj = self.registry('recurring.invoicer')
        invoicer_id = invoicer_obj.create(self.cr, self.uid, {})
        contract_group.generate_invoices(invoicer_id=invoicer_id)
        invoicer_obj.validate_invoices(self.cr, self.uid, [invoicer_id])
        invoice_ids = self.registry('account.invoice').search(
            self.cr, self.uid, [('recurring_invoicer_id', '=', invoicer_id)])
        return invoice_ids

    def _pay_invoices(self, invoice_ids):
        journal_obj = self.registry('account.journal')
        bank_journal_id = self.registry('account.journal').search(
            self.cr, self.uid, [('type', '=', 'bank')])[0]
        bank_journal = journal_obj.browse(self.cr, self.uid, bank_journal_id)
        account_id = self.registry('account.account').search(
            self.cr, self.uid, [('code', '=', '1050')])[0]
        move_obj = self.registry('account.move')
        move_line_obj = self.registry('account.move.line')
        for invoice in self.registry('account.invoice').browse(
                self.cr, self.uid, invoice_ids):
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
