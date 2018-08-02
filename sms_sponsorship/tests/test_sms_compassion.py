# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest

_logger = logging.getLogger(__name__)


class TestSmsCompassion(BaseSponsorshipTest):

    def setUp(self):
        super(TestSmsCompassion, self).setUp()
        self.child = self.create_child('AP2696234923')
        # self.child = self.env['compassion.child'].create({
        #     'global_id': 'AP1696234923',
        #     'local_id': 'GD21321'
        # })
        # self.child.hold_id.channel = 'sms'
        self.partner = self.env.ref('base.res_partner_2')

        self.child_request = self.env['sms.child.request'].create({
            'partner_id': self.partner.id,
            'sender': self.partner.phone,
            'child_id': self.child.id
        })

    def test_sms_sponsorship_creation(self):

        # test with new partner
        values = {
            'firstname': "testName",
            'lastname': 'testLastname',
            'phone': '1234567890',
            'email': 'test@email.com',
            'sponsorship_plus': False
        }
        self.env['recurring.contract']\
            .create_sms_sponsorship(values, False, self.child_request)
        new_partner = self.env['res.partner'].search([
            ('firstname', '=', "testName"),
            ('lastname', '=', 'testLastname'),
            ('email', '=', 'test@email.com')
        ])
        self.assertTrue(new_partner)
        self.assertTrue(self.child_request.new_partner)
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', new_partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ])
        self.assertTrue(new_sponsorship)

        # test with existing partner, but not given
        values = {
            'firstname': self.partner.firstname,
            'lastname': self.partner.lastname,
            'phone': self.partner.phone,
            'email': self.partner.email,
            'sponsorship_plus': False
        }
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, False, self.child_request)
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', self.partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertTrue(new_sponsorship)

        # test with given existing partner
        values = {
            'firstname': self.partner.firstname,
            'lastname': self.partner.lastname,
            'phone': self.partner.phone,
            'email': self.partner.email,
            'sponsorship_plus': False
        }
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, self.partner, self.child_request)
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', self.partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertTrue(new_sponsorship)

    def test_sms_request(self):
        values = {
            'firstname': self.partner.firstname,
            'lastname': self.partner.lastname,
            'phone': self.partner.phone,
            'email': self.partner.email,
            'sponsorship_plus': False
        }
        sms_request = self.child_request
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, self.partner, self.child_request)
        sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', self.partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertEquals(sms_request.sponsorship_id.id, sponsorship.id)

        self.assertFalse(sms_request.hold_id)
        sms_request.reserve_child()
        self.assertTrue(sms_request.hold_id)
        sms_request.cancel_request()
        self.assertFalse(sms_request.hold_id)
        sms_request.reserve_child()
        self.assertTrue(sms_request.hold_id)
        sms_request.cancel_request()
        self.assertFalse(sms_request.hold_id)

    def test_book_by_sms(self):
        pass
        # hold = self.child.hold_id
        # self.assertFalse(hold.sms_request_id)
        # TODO Patch the hold send and with_delay() to test child allocation
        # request = self.env['sms.child.request'].create({
        #     'sender': '+41213456789'
        # })
