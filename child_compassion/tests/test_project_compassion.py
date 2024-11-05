from odoo.tests import TransactionCase
from unittest.mock import Mock, patch

PROJECT_COMPASSION_ADDON = ("odoo.addons.child_compassion.models"
    ".project_compassion.CompassionProject")

class TestProjectCompassion(TransactionCase):
    
    @patch(f"{PROJECT_COMPASSION_ADDON}.update_informations")
    @patch(f"{PROJECT_COMPASSION_ADDON}.get_lifecycle_event")
    def test_sync_projects_from_gmc(self):
        # Mock methods which require an external API
        # TODO TEST
        projects = self.env["compassion.project"]
        projects.sync_projects_from_gmc()

        # projects.update_informations = Mock()
        # projects.get_lifecycle_event = Mock()



