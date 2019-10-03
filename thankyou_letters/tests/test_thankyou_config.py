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

        cls.config50 = cls.env['thankyou.config'].create({
            'min_donation_amount': 50.0,
            'send_mode': 'auto_digital_only',
        })
        cls.config100 = cls.env['thankyou.config'].create({
            'min_donation_amount': 100.0,
            'send_mode': 'physical',
        })
        cls.config500 = cls.env['thankyou.config'].create({
            'min_donation_amount': 500.0,
            'send_mode': 'physical',
        })

    def test_for_donation_amount(self):
        """
        Test the thankyou configuration selected depending on the donation
        amount.
        """
        thankyou_configs = self.env['thankyou.config'].search([])

        # Amount smaller than the minimum.
        self.assertEqual(thankyou_configs.for_donation_amount(20),
                         self.config50)

        self.assertEqual(thankyou_configs.for_donation_amount(200),
                         self.config100)

        self.assertEqual(thankyou_configs.for_donation_amount(2000),
                         self.config500)

    def test_build_inform_mode(self):
        """ Test separating send_message using communication config logic. """
        send_mode, auto = self.config50.build_inform_mode(self.asus)

        self.assertTrue(auto)
        self.assertEquals(send_mode, 'digital')
