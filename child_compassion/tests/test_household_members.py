from odoo.tests import TransactionCase, tagged

from odoo.addons.message_center_compassion.tools.load_mappings import load_mapping_files


@tagged("post_install", "-at_install")
class TestHouseholdMembers(TransactionCase):
    """T3697 The members sent by Connect replace the members of the household"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_mapping_files(
            cls.env,
            "child_compassion/static/mappings/",
            ["household_member.json", "household.json"],
        )
        cls.household_model = cls.env["compassion.household"]
        # Another family with a member of the same name
        cls.other_household = cls.household_model.create(
            [
                {
                    "household_id": "H-T3697-OTHER",
                    "member_ids": [
                        (0, 0, {"name": "T3697 Lucy", "role": "Sister"}),
                        (0, 0, {"name": "T3697 Paul", "role": "Father"}),
                    ],
                }
            ]
        )

    def _connect_household(self, members):
        return {
            "Household_ID": "H-T3697",
            "Household_Name": "T3697 family",
            "BeneficiaryHouseholdMemberList": [
                {"HouseholdMember_Name": name, "HouseholdMemberRole": role}
                for name, role in members
            ],
        }

    def _receive(self, members):
        """Same path as a child update: the household is created, or updated
        when it already exists (see compassion.household.create)."""
        vals = self.household_model.json_to_data(self._connect_household(members))
        self.household_model.create([vals])
        return self.household_model.search([("household_id", "=", "H-T3697")])

    def test_member_list_is_replaced(self):
        members = [
            ("T3697 Lucy", "Sister"),
            ("T3697 Peter", "Brother"),
            ("T3697 Mary", "Mother"),
        ]
        household = self._receive(members)
        self.assertEqual(len(household.member_ids), 3)
        # Receiving the same family again must not add members
        household = self._receive(members)
        household = self._receive(members)
        self.assertEqual(len(household), 1)
        self.assertEqual(len(household.member_ids), 3)
        self.assertEqual(household.nb_sisters, 1)
        self.assertEqual(household.nb_brothers, 1)

    def test_member_removed_in_connect(self):
        household = self._receive([("T3697 Lucy", "Sister"), ("T3697 John", "Brother")])
        household = self._receive([("T3697 Lucy", "Sister")])
        self.assertEqual(household.member_ids.mapped("name"), ["T3697 Lucy"])

    def test_other_household_untouched(self):
        self._receive([("T3697 Lucy", "Sister"), ("T3697 Paul", "Father")])
        self.assertEqual(len(self.other_household.member_ids), 2)
        self.assertEqual(
            set(self.other_household.member_ids.mapped("name")),
            {"T3697 Lucy", "T3697 Paul"},
        )
