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


from openerp.addons.contract_compassion.tests.test_base_module \
    import test_base_module
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)


class test_contract_compassion(test_base_module):
    """
        Test Project contract compassion.
        We are testing 3 scenarios :
         - in the first, we are testing the changement of state of a contract
         and we are testing what is happening when we pay an invoice.
         - in the second one, we are testing what is happening when we cancel
         a contract.
         - in the last one, we are testing the _reset_open_invoices method.
    """

    def setUp(self):
        super(test_contract_compassion, self).setUp()

    def test_contract_compassion_first_scenario(self):
        """
            In this test we are testing states changement of a contract and if
            the old invoice are well cancelled when we pay one invoice.
        """
        # Creation of a the next fiscal year
        next_year = (datetime.strptime(
            (datetime.today().strftime(DF)), DF)
            + relativedelta(years=+1)).year
        fiscal_year = self.env['account.fiscalyear'].create({
            'name': next_year,
            'code': next_year,
            'date_start': datetime.strptime((datetime(
                next_year, 1, 1)).strftime(DF), DF),
            'date_stop': datetime.strptime((datetime(
                next_year, 12, 31)).strftime(DF), DF),
            })
        fiscal_year.create_period()
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 5,
            self.payment_term_id, ref=None,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'phone', 'type': 'O'})
        self._create_contract_line(
            contract_id, '40.0', other_vals={'quantity': '2'})
        contract = self.env['recurring.contract'].browse(contract_id)
        self.assertEqual(contract.state, 'draft')

        # Switching to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        self.assertEqual(contract.state, 'waiting')

        invoices = contract.button_generate_invoices().invoice_ids
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 6)
        self.assertEqual(invoices[3].state, 'open')

        # Payment of the third invoice so the
        # contract will be on the active state and the 2 first invoices should
        # be cancelled.
        self._pay_invoice(invoices[3])
        self.assertEqual(invoices[3].state, 'paid')
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')
        self.assertEqual(invoices[2].state, 'cancel')
        self.assertEqual(invoices[4].state, 'open')
        self.assertEqual(invoices[5].state, 'open')
        self.assertEqual(contract.state, 'active')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        self.assertEqual(contract.state, 'terminated')

    def test_contract_compassion_second_scenario(self):
        """
            Testing if invoices are well cancelled when we cancel the related
            contract.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[1], 1,
            self.payment_term_id, ref=None,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'postal', 'type': 'O'})
        self._create_contract_line(
            contract_id, '200.0', other_vals={'quantity': '3'})
        contract = self.env['recurring.contract'].browse(contract_id)
        # Switch to "waiting for payment" state
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        invoices = contract.button_generate_invoices().invoice_ids
        self.assertEqual(invoices[0].state, 'open')
        self.assertEqual(invoices[1].state, 'open')
        self.assertEqual(len(invoices), 2)

        # Cancelling of the contract
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_terminated', self.cr)
        self.assertEqual(contract.state, 'cancelled')
        self.assertEqual(invoices[0].state, 'cancel')
        self.assertEqual(invoices[1].state, 'cancel')

    def test_reset_open_invoices(self):
        """
            Testing of the method that update invoices when the contract
            is updated.
            THe invoice paid should not be updated, whereas the other one
            should be updated.
        """
        contract_group = self._create_group(
            'do_nothing', self.partners.ids[0], 1,
            self.payment_term_id, ref=None,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_group2 = self._create_group(
            'do_nothing', self.partners.ids[1], 2,
            self.payment_term_id, ref=None,
            other_vals={'recurring_value': 1, 'recurring_unit': 'month'})
        contract_id = self._create_contract(
            datetime.today().strftime(DF), contract_group,
            datetime.today().strftime(DF),
            other_vals={'channel': 'postal', 'type': 'O'})
        contract_line_id = self._create_contract_line(
            contract_id, '60.0', other_vals={'quantity': '2'})
        contract = self.env['recurring.contract'].browse(contract_id)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            self.uid, 'recurring.contract',
            contract_id, 'contract_validated', self.cr)
        invoices = contract.button_generate_invoices().invoice_ids
        self._pay_invoice(invoices[0])
        self.assertEqual(len(invoices), 2)
        contract_line = self.env['recurring.contract.line'].browse(
            contract_line_id)
        # Updating of the contract
        contract_line.write({
            'quantity': '3',
            'amount': '100.0',
        })
        contract.write({
            'group_id': contract_group2})

        # Check if the invoice unpaid is well updated
        invoice_upd = invoices[1]
        invoice_line_up = invoice_upd.invoice_line[0]
        self.assertEqual(invoice_line_up.price_unit, contract_line.amount)
        self.assertEqual(
            invoice_line_up.price_subtotal, contract_line.subtotal)
