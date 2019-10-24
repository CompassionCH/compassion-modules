##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import datetime, timedelta

from .test_sponsorship_compassion import BaseSponsorshipTest


class TestSponsorshipImpact(BaseSponsorshipTest):

    def test_sponsorship_impact_first_scenario(self):
        self.env['thankyou.config'].create({
            'min_donation_amount': 50.0,
            'send_mode': 'auto_digital_only',
        })
        # Create 3 children and get the project associated
        child1 = self.create_child('PI012304561')
        child2 = self.create_child('PJ012304562')
        child3 = self.create_child('Pk012304563')

        # Set child3 as a girl
        child3.gender = u'F'

        # Creation of the sponsorship contract
        partner = self.michel
        sp_group = self.create_group({'partner_id': partner.id})
        sponsorship_ids = [
            self.create_contract(
                {
                    'partner_id': self.michel.id,
                    'group_id': sp_group.id,
                    'child_id': child1.id,
                },
                [{'amount': 50.0}]
            ),
            self.create_contract(
                {
                    'partner_id': self.michel.id,
                    'group_id': sp_group.id,
                    'child_id': child2.id,
                },
                [{'amount': 50.0}]
            ),
            self.create_contract(
                {
                    'partner_id': self.michel.id,
                    'group_id': sp_group.id,
                    'child_id': child3.id,
                },
                [{'amount': 50.0}]
            )]

        # Check that the children are sponsored
        self.assertEqual(child1.state, 'P')
        self.assertEqual(sponsorship_ids[0].state, 'draft')

        # Contract validation
        for sponsorship in sponsorship_ids:
            self.validate_sponsorship(sponsorship)

        invoices1 = sponsorship_ids[0].button_generate_invoices().invoice_ids

        invoice1 = self.env['account.invoice'].browse(invoices1[1].id)

        self._pay_invoice(invoice1)

        # change date of sponsorships
        now = datetime.now()
        create_date = (now - timedelta(weeks=8))
        for sponsorship in sponsorship_ids:
            sponsorship.create_date = create_date.strftime('%Y-%m-%d %H:%M:%S')
            sponsorship.activation_date = (create_date + timedelta(
                days=1)).strftime('%Y-%m-%d')
            sponsorship.start_date = (
                create_date + timedelta(days=2)).strftime('%Y-%m-%d')

        self.assertEqual(sponsorship_ids[0].state, 'active')
        self.assertEqual(partner.sr_sponsorship, 3)

        # Check duration : 8*7-2 = 52 days per sponsorship
        # self.assertEqual(partner.sr_time_fcp, 53 * 3)

        self.assertEqual(partner.sr_nb_girl, 1)
        self.assertEqual(partner.sr_nb_boy, 2)
