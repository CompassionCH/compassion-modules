from odoo.tests import common


class TestResPartner(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_1')
        self.product = self.env.ref('product.product_product_4')
        self.payment_term = self.env.ref('account.account_payment_term_immediate')
        self.invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'name': 'Invoice 1',
            'invoice_payment_term_id': self.payment_term.id,
            'invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 1, 'price_unit': 10.0})]
        })
        self.invoice.action_post()

    def test_write(self):
        # Test that updating the partner's payment term updates the payment term of the partner's unpaid invoices
        new_payment_term = self.env['account.payment.term'].create({'name': 'New Payment Term'})
        self.partner.write({'property_payment_term_id': new_payment_term.id})
        self.assertEqual(self.invoice.invoice_payment_term_id.id, new_payment_term.id)
