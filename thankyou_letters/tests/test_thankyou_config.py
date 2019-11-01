# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests import SavepointCase


class TestThankYouLetters(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestThankYouLetters, cls).setUpClass()
        cls.asus = cls.env.ref('base.res_partner_1')

        cls.config50 = cls.env.ref('thankyou_letters.thankyou_config_50')
        cls.config100 = cls.env.ref('thankyou_letters.thankyou_config_100')
        cls.config500 = cls.env.ref('thankyou_letters.thankyou_config_500')

    def test_for_donation_amount(self):
        """
        Test the thankyou configuration selected depending on the donation
        amount.
        """
        thankyou_configs = self.env['thankyou.config'].search([])

        # Amount smaller than the minimum.
        line = self.env['account.invoice.line'].search([
            ('price_subtotal', '<=', 20)
        ], limit=1)
        self.assertEqual(thankyou_configs.for_donation(line),
                         self.config50)

        line = self.env['account.invoice.line'].search([
            ('price_subtotal', '>=', 100),
            ('price_subtotal', '<', 500),
        ], limit=1)
        self.assertEqual(thankyou_configs.for_donation(line),
                         self.config100)

        line = self.env['account.invoice.line'].search([
            ('price_subtotal', '>=', 500),
        ], limit=1)
        self.assertEqual(thankyou_configs.for_donation(line),
                         self.config500)

    def test_build_inform_mode(self):
        """ Test separating send_message using communication config logic. """
        send_mode, auto = self.config50.build_inform_mode(self.asus)

        self.assertTrue(auto)
        self.assertEquals(send_mode, 'digital')
