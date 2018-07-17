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
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest

_logger = logging.getLogger(__name__)


class TestAnalyticAttribution(BaseSponsorshipTest):

    def setUp(self):
        super(TestAnalyticAttribution, self).setUp()
        self.child = self.create_child('UG1119182')
        self.rule = self.env.ref('sms_sponsorship.release_booking_by_sms_rule')

    def test_book_by_sms(self):
        hold = self.child.hold_id
        self.assertFalse(hold.booked_by_phone_number)
        self.child.hold_id.book_by_sms('021 345 67 89')
        self.assertTrue(hold.booked_by_phone_number)
