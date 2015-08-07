# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import date
from random import randint
import logging

logger = logging.getLogger(__name__)


class test_tracking(common.TransactionCase):
    """
    Test whole lifecycle of contracts and see if sds tracking information
    is correct.
    Warning : Please make sure module sponsorship_sync_gp is not installed
              in order to be sure no information is sent to GP.
    """

    def setUp(self):
        super(test_tracking, self).setUp()
        self.con_obj = self.registry('recurring.contract')
        self.child_obj = self.registry('compassion.child')
        self.today = date.today().strftime(DF)

    def _create_contract(self, child_id):
        """Creates a new contract for given child."""
        sponsor_category = self.registry('res.partner.category').search(
            self.cr, self.uid, [('name', 'ilike', 'sponsor')])
        partner_ids = self.registry('res.partner').search(
            self.cr, self.uid, [('category_id', 'in', sponsor_category)])
        origin_ids = self.registry('recurring.contract.origin').search(
            self.cr, self.uid, [('name', 'like', 'Other')])
        group_ids = self.registry('recurring.contract.group').search(
            self.cr, self.uid, [('partner_id', '=', partner_ids[0])])
        contract_vals = {
            'partner_id': partner_ids[0],
            'correspondant_id': partner_ids[0],
            'origin_id': origin_ids[0],
            'group_id': group_ids[0],
            'channel': 'direct',
            'num_pol_ga': randint(700, 999),
            'child_id': child_id,
            'next_invoice_date': self.today,
            'activation_date': self.today,
        }
        con_id = self.con_obj.create(self.cr, self.uid, contract_vals)
        return con_id

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
        child_keys = ["PE3760144", "IO6790212", "UG8320012", "UG8350016"]  # nopep8 (will be used)
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
