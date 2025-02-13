from unittest import mock

from .test_sponsorship_compassion import BaseSponsorshipTest

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)


class TestSWPConsistency(BaseSponsorshipTest):
    def create_inconsistent_contract(self, update_hold):
        return self.create_contract(
            {
                "type": "SWP",
                "correspondent_id": self.wp_partner.id,
                "partner_id": self.partner_1.id,
                "group_id": self.sp_group.id,
            },
            update_hold,
        )

    @mock.patch(mock_update_hold)
    def setUp(self, update_hold, *args, **kwargs):
        super().setUp(*args, **kwargs)

        partner = self.env["res.partner"]

        self.wp_partner = partner.create({"name": "WP Partner"})
        self.inconsistent_contract1 = self.create_inconsistent_contract(update_hold)
        self.inconsistent_contract2 = self.create_inconsistent_contract(update_hold)

        self.non_wp_partner = partner.create({"name": "Non WP Partner"})
        self.consistent_contract = self.create_contract(
            {
                "partner_id": self.non_wp_partner.id,
                "type": "S",
                "group_id": self.sp_group.id,
            },
            update_hold,
        )

    def test_fix_inconsistent_SWP_contracts(self):
        consistent_contract_lines_before = self.consistent_contract.contract_line_ids

        # Before the fix, no sponsorships are visible on the portal
        self.assertEqual(len(self.wp_partner.get_portal_sponsorships()), 0)

        self.env["recurring.contract"].fix_inconsistent_SWP_contracts()

        # After the fix, the WP partner can see their 2 sponsorships
        self.assertEqual(len(self.wp_partner.get_portal_sponsorships()), 2)

        # The consistent / normal contract should not have been changed
        self.assertEqual(self.consistent_contract.type, "S")
        self.assertEqual(
            consistent_contract_lines_before, self.consistent_contract.contract_line_ids
        )
