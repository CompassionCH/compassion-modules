##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Albert SHENOUDA <albert.shenouda@efrei.net>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime

from odoo.addons.recurring_contract.tests.test_recurring_contract import (
    BaseContractTest,
)

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

logger = logging.getLogger(__name__)


class BaseContractCompassionTest(BaseContractTest):
    def create_contract(self, vals, line_vals):
        # Add default values
        default_values = {"type": "O"}
        default_values.update(vals)
        return super().create_contract(default_values, line_vals)

    def _pay_invoice(self, invoice):
        bank_journal = self.env["account.journal"].search(
            [("code", "=", "BNK1")], limit=1
        )
        payment = self.env["account.payment"].create(
            {
                "journal_id": bank_journal.id,
                "amount": invoice.amount_total,
                "payment_date": invoice.date_due,
                "payment_type": "inbound",
                "payment_method_id": bank_journal.inbound_payment_method_ids[0].id,
                "partner_type": "customer",
                "partner_id": invoice.partner_id.id,
                "currency_id": invoice.currency_id.id,
                "invoice_ids": [(6, 0, invoice.ids)],
            }
        )
        payment.post()


class TestContractCompassion(BaseContractCompassionTest):
    """
        Test Project contract compassion.
        We are testing 3 scenarios :
         - in the first, we are testing the changement of state of a contract
         and we are testing what is happening when we pay an invoice.
         - in the second one, we are testing what is happening when we cancel
         a contract.
         - in the last one, we are testing the _reset_open_invoices method.
    """

    def test_contract_compassion_first_scenario(self):
        """
            In this test we are testing states changement of a contract and if
            the old invoice are well cancelled when we pay one invoice.
        """
        contract_group = self.create_group(
            {"advance_billing_months": 5, "partner_id": self.michel.id}
        )
        contract = self.create_contract(
            {"partner_id": self.michel.id, "group_id": contract_group.id, },
            [{"amount": 40.0}],
        )
        self.assertEqual(contract.state, "draft")

        # Switching to "waiting for payment" state
        contract.contract_waiting()
        self.assertEqual(contract.state, "waiting")

        invoices = contract.button_generate_invoices().invoice_ids.sorted(
            "date_invoice", reverse=True
        )
        nb_invoices = len(invoices)
        self.assertEqual(nb_invoices, 6)
        self.assertEqual(invoices[3].state, "open")

        # Payment of the third invoice so the
        # contract will be on the active state and the 2 first invoices should
        # be cancelled.
        self._pay_invoice(invoices[3])
        # For now the test is broken because cancel invoices are done in job.
        # TODO Would be better to launch job synchronously in the test:
        # https://github.com/OCA/queue/issues/89
        # self.assertEqual(invoices[3].state, 'paid')
        # self.assertEqual(invoices[0].state, 'open')
        # self.assertEqual(invoices[1].state, 'open')
        # self.assertEqual(invoices[2].state, 'open')
        # self.assertEqual(invoices[4].state, 'cancel')
        # self.assertEqual(invoices[5].state, 'cancel')
        self.assertEqual(contract.state, "active")
        contract.contract_terminated()
        self.assertEqual(contract.state, "terminated")

    def test_contract_compassion_second_scenario(self):
        """
            Testing if invoices are well cancelled when we cancel the related
            contract.
        """
        contract_group = self.create_group({"partner_id": self.thomas.id})
        contract = self.create_contract(
            {"partner_id": self.thomas.id, "group_id": contract_group.id, },
            [{"amount": 200, "quantity": 3}],
        )

        # Switch to "waiting for payment" state
        contract.contract_waiting()
        invoices = contract.button_generate_invoices().invoice_ids
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].state, "open")
        self.assertEqual(invoices[1].state, "open")

        # Cancelling of the contract
        contract.contract_cancelled()
        # Force cleaning invoices immediately
        contract._clean_invoices()
        self.assertEqual(contract.state, "cancelled")
        self.assertEqual(invoices[0].state, "cancel")
        self.assertEqual(invoices[1].state, "cancel")

    def test_reset_open_invoices(self):
        """
            Testing of the method that update invoices when the contract
            is updated.
            THe invoice paid should not be updated, whereas the other one
            should be updated.
        """
        contract_group = self.create_group({"partner_id": self.michel.id})
        contract_group2 = self.create_group(
            {"partner_id": self.david.id, "advance_billing_months": 2}
        )
        contract = self.create_contract(
            {"partner_id": self.michel.id, "group_id": contract_group.id, },
            [{"amount": 60.0, "quantity": 2}],
        )
        contract.contract_waiting()
        invoices = contract.button_generate_invoices().invoice_ids
        self.assertEqual(len(invoices), 2)
        self._pay_invoice(invoices[1])
        # Updating of the contract
        contract.contract_line_ids.write(
            {"quantity": "3", "amount": "100.0", }
        )
        contract.write({"group_id": contract_group2.id})

        # Check if the invoice unpaid is well updated
        invoice_upd = invoices[0]
        invoice_line_up = invoice_upd.invoice_line_ids[0]
        contract_line = contract.contract_line_ids
        self.assertEqual(invoice_line_up.price_unit, contract_line.amount)
        self.assertEqual(invoice_line_up.price_subtotal, contract_line.subtotal)

    def _test_contract_compassion_third_scenario(self):
        """
            Test the changement of a partner in a payment option and after that
            changement test if the BVR reference is set.
            Test the changement of the payment term and set it to the BVR one
            and check if the payment option of the contract has the good
            payment term.
            Test the changement of a payment option for a contract.
        """
        contract_group = self.create_group(
            "do_nothing",
            self.partners.ids[0],
            1,
            self.payment_mode_id,
            other_vals={"recurring_value": 1, "recurring_unit": "month"},
        )
        contract_group2 = self.create_group(
            "do_nothing",
            self.partners.ids[1],
            1,
            self.payment_mode_id,
            other_vals={"recurring_value": 1, "recurring_unit": "month"},
        )
        contract = self.create_contract(
            datetime.today().strftime(DF),
            contract_group,
            datetime.today().strftime(DF),
            other_vals={"type": "O"},
        )
        contract_group.write({"partner_id": self.partners.ids[1]})
        contract_group.on_change_partner_id()
        self.assertTrue(contract_group.bvr_reference)
        payment_mode_2 = self.env.ref("account_payment_mode.payment_mode_inbound_dd1")
        contract_group2.write({"payment_mode_id": payment_mode_2.id})
        contract_group2.on_change_payment_mode()
        self.assertTrue(contract_group2.bvr_reference)
        contract.contract_waiting()
        contract.write({"group_id": contract_group2.id})
        contract.on_change_group_id()
        self.assertEqual(contract.group_id.payment_mode_id, payment_mode_2)
