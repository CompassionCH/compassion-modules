# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest


class TestTracking(BaseSponsorshipTest):
    """
    Test whole lifecycle of contracts and see if sds tracking information
    is correct.
    Warning : Please make sure module sponsorship_sync_gp is not installed
              in order to be sure no information is sent to GP.
    """

    def setUp(self):
        super(TestTracking, self).setUp()

    def test_contract_tracking_until_sub_sponsorship_made(self):
        """
        Test scenario:
            1. Four new contracts waiting payment
            2. Contracts activated
            3. Four Child departures
            4. SUB Sponsorship for all contracts
            5a. Two SUB Acceptance
                - one regular acceptance
                - one sub sponsorship was not accepted by sponsor, but he
                  chose another child instead and paid it.
            5b. One SUB Reject
            5c. One with No Sub contract
        """
        # Four child codes available for testing
        # child_keys = ["PE3760144", "IO6790212", "UG8320012", "UG8350016"]
        # TODO Implement this test
        return True

    def test_project_tracking(self):
        """
        Test scenario:
            1. Two contracts activated
            2. Two Projects become fund-suspended
            3. Project A:
                a. suspension extension
                b. sponsor is not informed
                c. project becomes phase-out
                d. sponsor is alerted
            4. Project B:
                a. sponsor is informed
                b. project is reactivated
                c. funds are attributed
        """
        # TODO Implement the test
        return True
