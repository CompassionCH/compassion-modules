"""
Test moved here because of circular dependencies between sponsorship_compassion and
child_compassion
"""

import random
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase
from odoo.tools import relativedelta

PROJECT_COMPASSION_ADDON = (
    "odoo.addons.child_compassion.models.project_compassion.CompassionProject"
)


class TestProjectCompassion(TransactionCase):
    def create_project(self, with_sponsorship=True):
        partner = self.env["res.partner"].create(
            {"name": "Test Partner", "portal_sponsorships": "all"}
        )
        last_update = fields.Date.today() - relativedelta(days=142)
        project = self.env["compassion.project"].create(
            {
                "fcp_id": f"test_fcp_id_{random.randint(1, 1e9)}",
                "last_update_date": last_update,
            }
        )
        project.status = "Active"
        if with_sponsorship:
            child = self.env["compassion.child"].create(
                {
                    "name": "Test Child",
                    "global_id": f"test_global_id{random.randint(1, 1e9)}",
                    "project_id": project.id,
                }
            )
            contract_group = self.env["recurring.contract.group"].create(
                {"partner_id": partner.id}
            )
            self.env["recurring.contract"].create(
                {
                    "child_id": child.id,
                    "partner_id": partner.id,
                    "group_id": contract_group.id,
                    "pricelist_id": 1,
                }
            )
        return project

    def setUp(self):
        super().setUp()

        self.projects_with_sponsorships = [
            self.create_project(with_sponsorship=True) for _ in range(42)
        ]
        self.projects_without_sponsorships = [
            self.create_project(with_sponsorship=False) for _ in range(76)
        ]

    @patch(f"{PROJECT_COMPASSION_ADDON}.update_informations")
    @patch(f"{PROJECT_COMPASSION_ADDON}.get_lifecycle_event")
    def test_sync_projects_from_gmc_logic(
        self, mock_update_informations, mock_get_lifecycle_event
    ):
        expected_nb_projects_updated = len(self.projects_with_sponsorships)

        projects = self.env["compassion.project"]
        projects.sync_projects_from_gmc(
            requests_throttle_seconds=0.01,
        )

        self.assertEqual(
            mock_update_informations.call_count, expected_nb_projects_updated
        )

        self.assertEqual(
            mock_get_lifecycle_event.call_count, expected_nb_projects_updated
        )
