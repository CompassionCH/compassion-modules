from odoo.exceptions import ValidationError
from odoo.tests import SingleTransactionCase

from ..tools.load_mappings import load_mapping_files


class TestMapping(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_advanced_query_mapping_loaded(self):
        """Test that the advanced query mapping is correctly loaded after
        module installation."""
        query_mapping = self.env["compassion.mapping"].search(
            [("name", "=", "advanced query")]
        )
        self.assertTrue(query_mapping)
        self.assertEqual(query_mapping.model_id.model, "compassion.query.filter")
        json_specs = query_mapping.json_spec_ids
        # The field mapping should be a relational field mapping
        field_mapping = json_specs.filtered("relational_field_id")
        self.assertEqual(field_mapping.field_name, "id")
        self.assertEqual(field_mapping.relational_field_id.name, "field_id")
        self.assertEqual(field_mapping.json_name, "Field")

    def test_json_mapping_loader(self):
        path = "message_center_compassion/static/mappings/"
        files = ["res_partner_test_mapping.json", "res_user_test_mapping.json"]
        # Loading the res.user mapping will raise an error
        # because res.user is not a mapped.model
        with self.assertRaises(ValidationError):
            load_mapping_files(self.env.cr, path, files)

        # Load the res.partner mapping
        load_mapping_files(self.env.cr, path, files[:1])
        partner_mapping = self.env["compassion.mapping"].search(
            [("model_id.model", "=", "res.partner")]
        )
        self.assertTrue(partner_mapping)
