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
from mock import mock
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion\
    import BaseSponsorshipTest

mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_release_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                     '.CompassionHold.release_hold')
mock_get_infos = ('odoo.addons.child_compassion.models.child_compassion'
                  '.CompassionChild.get_infos')
mock_invoicer = ('odoo.addons.recurring_contract.models.contract_group'
                 '.ContractGroup.generate_invoices')
mock_cleaner = ('odoo.addons.recurring_contract.models.recurring_contract'
                '.RecurringContract.clean_invoices')


class TestTracking(BaseSponsorshipTest):
    """
    Test whole lifecycle of contracts and see if sds tracking information
    is correct.
    Warning : Please make sure module sponsorship_sync_gp is not installed
              in order to be sure no information is sent to GP.
    """

    def setUp(self):
        super(TestTracking, self).setUp()

        self.thomas = self.env.ref('base.res_partner_address_3')
        self.michel = self.env.ref('base.res_partner_address_4')
        self.david = self.env.ref('base.res_partner_address_10')
        self.jacob = self.env.ref('base.res_partner_address_25')

        # Creating childs and sponsorships contracts
        child1 = self.create_child('PE3760144')
        sp_group = self.create_group({'partner_id': self.michel.id})
        sponsorship1 = self.create_contract(
            {
                'partner_id': self.michel.id,
                'group_id': sp_group.id,
                'child_id': child1.id,
                'global_id': 'wlefkjewf'
            },
            [{'amount': 50.0}]
        )

        child2 = self.create_child('IO6790212')
        sp_group = self.create_group({'partner_id': self.thomas.id})
        sponsorship2 = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': sp_group.id,
                'child_id': child2.id,
                'global_id': 'wlefkdfjewf'
            },
            [{'amount': 50.0}]
        )

        child3 = self.create_child('UG8320012')
        sp_group = self.create_group({'partner_id': self.david.id})
        sponsorship3 = self.create_contract(
            {
                'partner_id': self.david.id,
                'group_id': sp_group.id,
                'child_id': child3.id,
                'global_id': 'wlefkjewe34wf'
            },
            [{'amount': 50.0}]
        )

        child4 = self.create_child('UG8350016')
        sp_group = self.create_group({'partner_id': self.jacob.id})
        sponsorship4 = self.create_contract(
            {
                'partner_id': self.jacob.id,
                'group_id': sp_group.id,
                'child_id': child4.id,
                'global_id': 'wle234534fkjewf'
            },
            [{'amount': 50.0}]

        )

        list_sponsorships = self.env['recurring.contract'].with_context(
            async_mode=True)

        list_sponsorships += sponsorship1
        list_sponsorships += sponsorship2
        list_sponsorships += sponsorship3
        list_sponsorships += sponsorship4
        self.list_sponsorships = list_sponsorships

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_infos)
    @mock.patch(mock_invoicer)
    @mock.patch(mock_cleaner)
    @mock.patch(mock_release_hold)
    def test_contract_tracking_until_sub_sponsorship_made(
            self, release_mock, cleaner, invoicer, get_infos, hold_mock):
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
        hold_mock.return_value = True
        get_infos.return_value = True
        invoicer.return_value = True
        cleaner.return_value = True
        release_mock.return_value = True

        # Activate the sponsorships contracts and make the depart of child
        self.list_sponsorships.with_context(async_mode=True).force_activation()
        for subsponsorship in self.list_sponsorships:
            self.assertEqual(subsponsorship.sds_state, 'active')

        list_childs = self.list_sponsorships.mapped('child_id')
        list_childs.depart()

        for subsponsorship in self.list_sponsorships:
            self.assertEqual(subsponsorship.sds_state, 'sub_waiting')

        sub_child1 = self.create_child('PE47601334')
        sub_child2 = self.create_child('PE57601335')
        sub_child3 = self.create_child('PE67601336')
        sub_child4 = self.create_child('PE87601336')

        # Regular sub
        # Create a subsponsorship and get its id.
        sub1_id = self.env['sds.subsponsorship.wizard'].with_context(
            active_id=self.list_sponsorships[0].id
        ).create({'state': 'sub',
                  'channel': 'direct',
                  'child_id': sub_child1.id}).create_subsponsorship()['res_id']
        # Get the subsponsorship from its id and force his activation.
        self.assertEqual(self.list_sponsorships[0].sds_state, 'sub')
        subsponsorship1 = self.env['recurring.contract'].browse(sub1_id)
        subsponsorship1.with_context(async_mode=True).force_activation()
        self.list_sponsorships[0].sds_state_date = '2017-11-01'
        self.list_sponsorships[0].check_sub_state()

        self.assertEqual(self.list_sponsorships[0].sds_state, 'sub_accept')
        self.assertEqual(subsponsorship1.sds_state, 'active')

        # Sponsor choose another child
        subsponsorship2_wizzard = self.env['sds.subsponsorship.wizard'].\
            with_context(active_id=self.list_sponsorships[1].id).create({
                'state': 'sub',
                'channel': 'direct',
                'child_id': sub_child2.id})

        sub2_id = subsponsorship2_wizzard.create_subsponsorship()['res_id']
        subsponsorship2 = self.env['recurring.contract'].browse(sub2_id)
        self.assertEqual(self.list_sponsorships[1].sds_state, 'sub')
        subsponsorship2.with_context(async_mode=True).force_activation()

        # The subsponsorship is ended, the sponsor choose another child.
        exchange = self.env.ref(
            'sponsorship_compassion.end_reason_child_exchange')
        self.env['end.contract.wizard'].with_context(default_type='S').create({
            'contract_id': subsponsorship2.id,
            'end_reason_id': exchange.id}).end_contract()

        self.assertEqual(self.list_sponsorships[1].sds_state, 'sub')

        subsponsorship3_2 = self.create_contract(
            {
                'partner_id': subsponsorship2.partner_id.id,
                'group_id': subsponsorship2.group_id.id,
                'child_id': sub_child4.id,
                'parent_id': self.list_sponsorships[1].id,
                'global_id': 'wle2dsg34fkjewf'
            },
            [{'amount': 50.0}]

        )
        subsponsorship3_2.with_context(async_mode=True).force_activation()
        self.list_sponsorships[1].sds_state_date = '2017-11-01'
        self.list_sponsorships[1].check_sub_state()

        self.assertEqual(subsponsorship2.sds_state, 'cancelled')
        self.assertEqual(self.list_sponsorships[1].sds_state, 'sub_accept')
        self.assertEqual(subsponsorship3_2.sds_state, 'active')

        # One SUB Reject
        # Create sub sponsorship wizard, create a sponsorship from it and get
        # its id.
        sub3_id = self.env['sds.subsponsorship.wizard'].with_context(
            active_id=self.list_sponsorships[2].id).create({
                'state': 'sub', 'channel': 'direct', 'child_id': sub_child3.id}
            ).create_subsponsorship()['res_id']
        # Force th activation of the sponsorship we just created.
        subsponsorship3 = self.env['recurring.contract'].browse(sub3_id)
        subsponsorship3.with_context(async_mode=True).force_activation()

        self.assertEqual(self.list_sponsorships[2].sds_state, 'sub')
        # Setup a sponsorship end wizard and put and end to the subsponsorship
        # that we just created.
        subreject = self.env.ref('sponsorship_compassion.end_reason_subreject')
        self.env['end.contract.wizard'].with_context(default_type='S').create(
            {'contract_id': subsponsorship3.id,
             'end_reason_id': subreject.id}).end_contract()

        self.assertEqual(self.list_sponsorships[2].sds_state, 'sub_reject')
        self.assertEqual(subsponsorship3.sds_state, 'cancelled')

        # One with No Sub contract
        self.env['sds.subsponsorship.wizard'].with_context(
            active_id=self.list_sponsorships[3].id).create({
                'state': 'no_sub', 'channel': 'direct',
                'no_sub_default_reasons': 'not_given'}).no_sub()

        self.assertEqual(self.list_sponsorships[3].sds_state, 'no_sub')

        # Four child codes available for testing
        # child_keys = ["PE3760144", "IO6790212", "UG8320012", "UG8350016"]
        return True
