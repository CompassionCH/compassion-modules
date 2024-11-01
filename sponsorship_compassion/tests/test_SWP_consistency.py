from unittest import mock
from .test_sponsorship_compassion import BaseSponsorshipTest

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)


class TestSWPConsistency(BaseSponsorshipTest):

    def create_inconsistent_contract(self, update_hold):
        return self.create_contract(
            {
                "type": "O",  # given that the correspondent is W&P, this is inconsistent
                "correspondent_id": self.wp_partner.id,
                "partner_id": self.partner_1.id,
                "group_id": self.sp_group.id,
            },
            update_hold,
        )

    @mock.patch(mock_update_hold)
    def setUp(self, update_hold, *args, **kwargs):
        super(TestSWPConsistency, self).setUp(*args, **kwargs)

        wp_category = self.env["res.partner.category"].create({"name": "W&P"})
        partner = self.env["res.partner"]

        self.wp_partner = partner.create(
            {"name": "WP Partner", "category_id": wp_category}
        )
        self.inconsistent_contract1 = self.create_inconsistent_contract(update_hold)
        self.inconsistent_contract2 = self.create_inconsistent_contract(update_hold)

        self.non_wp_partner = partner.create({"name": "Non WP Partner"})
        self.consistent_contract = self.create_contract(
            {
                "partner_id": self.non_wp_partner.id,
                "type": "O",
                "group_id": self.sp_group.id,
            },
            update_hold,
        )

    def test_fix_inconsistent_SWP_contracts(self):
        self.env["recurring.contract"].fix_inconsistent_SWP_contracts()

        # The inconsistent contracts should have been fixed
        self.assertEqual(self.inconsistent_contract1.type, "SWP")
        self.assertEqual(self.inconsistent_contract2.type, "SWP")
        # The consistent / normal contract should not have been changed
        self.assertEqual(self.consistent_contract.type, "O")
