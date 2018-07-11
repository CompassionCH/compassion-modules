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
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest

_logger = logging.getLogger(__name__)


# todo tests don't work
class TestMobileAppConnector(BaseSponsorshipTest):

    def setUp(self):
        super(TestMobileAppConnector, self).setUp()

    def test_sponsor_children(self):
        child = self.create_child('UG4239181')
        partner = self.env.ref('base.res_partner_address_10')
        partner.ref = 'myref'
        child.partner_id = partner

        res = child.mobile_sponsor_children(userid=partner.ref)

        self.assertEqual(res, [])

    def test_fetch_letters(self):
        child = self.create_child('UG4239181')
        partner = self.env.ref('base.res_partner_address_10')
        partner.ref = 'myref'
        child.partner_id = partner

        res = child.mobile_get_letters(userid=partner.ref, supgrpid=12,
                                      needid=40)

        self.assertEqual(res, [])
