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

import mock

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest, mock_update_hold

_logger = logging.getLogger(__name__)


class TestSmsCompassion(BaseSponsorshipTest):

    def setUp(self):
        super().setUp()
        self.child = self.create_child('PE012304567')

        self.partner = self.env.ref('base.res_partner_2')
        self.env['ir.config_parameter'].set_param('web.external.url', 'base/')
        self.child_request = self.env['sms.child.request'].create({
            'partner_id': self.partner.id,
            'sender': self.partner.phone,
            'child_id': self.child.id,
            'lang_code': 'en_US'
        })

    @mock.patch(mock_update_hold)
    def test_sms_sponsorship_creation__with_new_partner(self, update_hold):
        update_hold.return_value = True
        values = {
            'firstname': "testName",
            'lastname': 'testLastname',
            'mobile': '1234567890',
            'email': 'test@email.com',
            'sponsorship_plus': False,
            'lang': 'en',
        }
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, False, self.child_request)
        new_partner = self.env['res.partner'].search([
            ('firstname', '=', "testName"),
            ('lastname', '=', 'testLastname'),
            ('email', '=', 'test@email.com')
        ])
        self.assertTrue(new_partner)
        self.assertEqual(new_partner.lang, 'en_US')
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', new_partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ])
        self.assertTrue(new_sponsorship)

    @mock.patch(mock_update_hold)
    def test_sms_sponsorship_creation__with_existing_partner(self, update_hold):
        update_hold.return_value = True

        new_partner2 = self.env['res.partner'].create({
            'firstname': "testName2",
            'lastname': 'testLastname2',
            'email': 'test2@email.com',
        })
        values = {
            'firstname': new_partner2.firstname,
            'lastname': new_partner2.lastname,
            'mobile': '001123456789',
            'email': new_partner2.email,
            'sponsorship_plus': False,
            'lang': 'en',
        }
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, False, self.child_request)
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', new_partner2.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertTrue(new_sponsorship)

        # test with given existing partner
        values = {
            'firstname': self.partner.firstname,
            'lastname': self.partner.lastname,
            'mobile': self.partner.mobile,
            'email': self.partner.email,
            'sponsorship_plus': False,
            'lang': 'en',
        }
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, self.partner, self.child_request)
        new_sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', self.partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertTrue(new_sponsorship)

    @mock.patch(mock_update_hold)
    def test_sms_request(self, update_hold):
        update_hold.return_value = True
        values = {
            'firstname': self.partner.firstname,
            'lastname': self.partner.lastname,
            'mobile': self.partner.phone,
            'email': self.partner.email,
            'sponsorship_plus': False,
            'lang': 'en',
        }
        sms_request = self.child_request
        self.env['recurring.contract'] \
            .create_sms_sponsorship(values, self.partner, self.child_request)
        sponsorship = self.env['recurring.contract'].search([
            ('partner_id', '=', self.partner.id),
            ('child_id', '=', self.child_request.child_id.id)
        ], limit=1)
        self.assertEqual(sms_request.sponsorship_id.id, sponsorship.id)

    def test_book_by_sms(self):
        pass
        # hold = self.child.hold_id
        # self.assertFalse(hold.sms_request_id)
        # TODO Patch the hold send and with_delay() to test child allocation
        # request = self.env['sms.child.request'].create({
        #     'sender': '+41213456789'
        # })
