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
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest

_logger = logging.getLogger(__name__)


class TestSmsCompassion(BaseSponsorshipTest):

    def setUp(self):
        super(TestSmsCompassion, self).setUp()
        self.child = self.create_child('UG1119182')
        self.child.hold_id.channel = 'sms'

    def test_book_by_sms(self):
        hold = self.child.hold_id
        self.assertFalse(hold.sms_request_id)
        # TODO Patch the hold send and with_delay() to test child allocation
        # request = self.env['sms.child.request'].create({
        #     'sender': '+41213456789'
        # })
