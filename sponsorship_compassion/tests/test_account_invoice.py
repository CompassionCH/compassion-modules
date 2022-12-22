import datetime

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

@tagged('post_install', '-at_install', 'only_this')
class AccountInvoiceTestCase(AccountTestInvoicingCommon):

    def test_build_invoice_data(self):
        # First part with an amount that isn't equal to 0
        # retrieve/create data for the test case
        amt = 20
        due_date = datetime.date.today().replace(year=2050)
        inv = self._generate_basic_invoice()
        dict_to_except = dict()
        dict_to_except[inv.name] = {
            "invoice_line_ids": inv._build_invoice_line(amt),
            "date": due_date
        }
        # Method to be tested
        dict_to_test = inv._build_invoice_data(amt=amt, due_date=due_date)
        self.assertDictEqual(dict_to_except, dict_to_test)

        # Second part with an amount that is equal to 0
        amt = 0
        dict_to_except[inv.name]['invoice_line_ids'] = "to_cancel"
        # Method to test
        dict_to_test = inv._build_invoice_data(amt=amt, due_date=due_date)
        self.assertDictEqual(dict_to_except, dict_to_test)


    def test_build_invoice_line(self):
        # retrieve/create data for the test case
        amt = 100
        inv = self._generate_basic_invoice()
        list_to_except = [(1, inv.invoice_line_ids.id,
                           {
                               "price_unit": amt
                           }
                           )]
        # Method to test
        list_to_test = inv._build_invoice_line(amt)
        self.assertListEqual(list_to_except, list_to_test)


    def test_cancel_invoice(self):
        inv = self._generate_basic_invoice()
        inv._cancel_invoice()
        self.assertEqual("cancel", inv.state)

    def test_update_invoice(self):
        # !!!!!! this test doesn't test the case with a recordset of invoices given
        # First case
        # Invoice has an amount
        inv = self._generate_basic_invoice()
        data_for_updt = dict()
        data_for_updt[inv.name] = {
            "invoice_line_ids": [(1, inv.invoice_line_ids.id, {"price_unit": 900})],
            "date": datetime.date.today().replace(year=2050)
        }
        # Method to test
        inv.update_invoices(data_for_updt)
        self.assertEqual(900, inv.invoice_line_ids.price_unit)
        self.assertEqual(datetime.date.today().replace(year=2050), inv.date)
        self.assertEqual("posted", inv.state)

        # Second case
        # Invoice has to be canceled
        data_for_updt[inv.name] = {"invoice_line_ids": "to_cancel"}
        inv.update_invoices(data_for_updt)
        self.assertEqual("cancel", inv.state)

    def _generate_basic_invoice(self):
        account = self.company_data['default_account_revenue']
        return self.env['account.move'].with_context(check_move_validity=False).create({
            'move_type': 'entry',
            'date': '2019-01-01',
            'line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'currency_id': self.currency_data['currency'].id,
                    'price_unit': 200
                }),
            ],
        })