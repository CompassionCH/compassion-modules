from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged, common


@tagged('post_install', '-at_install', 'only_this')
class TestGift(common.TransactionCase):
    def test_compute_date_gift_invoice(self):
        # Create a gift wizard with a gift event date in the future
        gift_event_date = date.today() + relativedelta(months=3)
        self.product = self.env.ref('product.product_product_4')
        gift_wizard = self.env['generate.gift.wizard'].create({
            'product_id': self.product.id,
            'amount': 10.0,
            'invoice_date': gift_event_date
        })

        # Test that the invoice due date is two months before the gift event date
        invoice_due_date = gift_event_date + relativedelta(months=-2)
        new_date, late = gift_wizard.compute_date_gift_invoice(gift_event_date, date.today())
        self.assertEqual(new_date, invoice_due_date)
        self.assertFalse(late)

        # Test that if the gift event date is less than two months from the invoice due date,
        # the invoice due date is not changed
        gift_event_date = date.today() + relativedelta(months=1)
        invoice_due_date = date.today()
        new_date, late = gift_wizard.compute_date_gift_invoice(gift_event_date, invoice_due_date)
        self.assertEqual(new_date, invoice_due_date)
        self.assertFalse(late)

        # Test that if the invoice due date is later than the gift event date, the invoice due date is set to
        # two months before the gift event date for next year
        gift_event_date = date.today() - relativedelta(months=3)
        invoice_due_date = gift_event_date + relativedelta(months=-2, years=+1)
        new_date, late = gift_wizard.compute_date_gift_invoice(gift_event_date, date.today() + relativedelta(years=1))
        self.assertEqual(new_date, invoice_due_date)
        self.assertFalse(late)
