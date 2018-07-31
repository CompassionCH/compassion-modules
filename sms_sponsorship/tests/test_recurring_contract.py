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


class TestSmsRecurringContract(BaseSponsorshipTest):

    def setUp(self):
        super(TestSmsRecurringContract, self).setUp()
        self.child = self.create_child('ZZ12611019')
        self.child.hold_id.channel = 'sms'
        self.env['ir.config_parameter'].set_param('web.external.url', 'base/')

    def test_create_sms_sponsorship(self):
        input = {
            'firstname': 'Jason',
            'lastname': 'Smith',
            'phone': '+41000000000',
            'email': 'jason@smith.com',
            'sponsorship_plus': True
        }
        sms_request = self.env['sms.child.request'] \
            .with_context(lang='fr_FR') \
            .create({'sender': '+41000000000'})

        self.env['recurring.contract'] \
            .create_sms_sponsorship(input, None, sms_request)
        self.assertTrue(sms_request.partner_id)
