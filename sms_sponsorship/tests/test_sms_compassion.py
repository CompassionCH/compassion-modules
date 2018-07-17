# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import regex
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest
from odoo import fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestSmsCompassion(BaseSponsorshipTest):

    def setUp(self):
        super(TestSmsCompassion, self).setUp()
        self.child = self.create_child('UG1119182')
        self.rule = self.env.ref('sms_sponsorship.release_booking_by_sms_rule')

    def test_book_by_sms__and_eviction_rule(self):
        hold = self.child.hold_id
        self.assertFalse(hold.booked_by_phone_number)
        hold.book_by_sms('+41213456789')
        self.assertTrue(hold.booked_by_phone_number)

        hold.booked_by_sms_at = fields.Datetime.from_string('2018-01-01')
        self.rule._check()
        self.assertFalse(hold.booked_by_phone_number)
        self.assertFalse(hold.booked_by_sms_at)

    def test_book_by_sms__should_fail_if_already_booked(self):
        hold = self.child.hold_id
        self.assertFalse(hold.booked_by_phone_number)
        hold.book_by_sms('+41213456789')
        with self.assertRaises(UserError):
            hold.book_by_sms('+41213456789')

    def test_book_by_sms__generate_url_of_next_step(self):
        hold = self.child.hold_id
        hold.book_by_sms('+41213456789')

        url = hold.generate_url_of_next_sms_sponsoring_step()
        self.assertRegexpMatches(url, r'sms-sponsorship/\d+/unknown-partner')
