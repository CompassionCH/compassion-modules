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

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

_logger = logging.getLogger(__name__)


# todo tests don't work
class TestMobileAppConnector(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref("base.res_partner_address_10")
        self.partner.ref = "myref"
        self.child = self.create_child("UG4239181")
        sp_group = self.create_group({"partner_id": self.partner.id})
        # Associate child and sponsor
        self.create_contract(
            {
                "partner_id": self.partner.id,
                "group_id": sp_group.id,
                "child_id": self.child.id,
            },
            [{"amount": 50.0}],
        )

    def test_sponsor_children(self):
        res = self.child.mobile_sponsor_children(userid=self.partner.ref)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        child_data = res[0]
        self.assertEqual(child_data.get("NeedKey"), "UG4239181")

    def test_fetch_letters(self):
        res = self.env["correspondence"].mobile_get_letters(
            userid=self.partner.ref, supgrpid=12, needid=40
        )

        self.assertEqual(res, [])
