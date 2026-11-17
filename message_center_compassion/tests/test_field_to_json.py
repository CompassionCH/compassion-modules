from odoo.tests import TransactionCase


class TestFieldToJson(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mapping = cls.env["compassion.mapping"].create(
            {
                "name": "Testing selection mapping",
                "model_id": cls.env.ref("base.model_res_partner").id,
            }
        )
        spec_obj = cls.env["compassion.field.to.json"]
        cls.spec = spec_obj.create(
            {"mapping_id": mapping.id, "json_name": "Type", "odoo_field": "type"}
        )
        cls.converted_spec = spec_obj.create(
            {
                "mapping_id": mapping.id,
                "json_name": "ConvertedType",
                "odoo_field": "type",
                "from_json_conversion": "json_value.split(' ')[0]",
            }
        )

    def test_selection_exact_and_casing(self):
        """GMC picklist values are matched to selection keys case-insensitively."""
        self.assertEqual(self.spec.field_id.ttype, "selection")
        self.assertEqual(self.spec.from_json("invoice"), {"type": "invoice"})
        self.assertEqual(self.spec.from_json("INVOICE"), {"type": "invoice"})
        self.assertEqual(self.spec.from_json("Delivery"), {"type": "delivery"})

    def test_selection_after_conversion(self):
        """Matching is done on the value returned by from_json_conversion."""
        self.assertEqual(
            self.converted_spec.from_json("Invoice address"), {"type": "invoice"}
        )

    def test_selection_unknown_value(self):
        """Unknown values are skipped with a warning instead of failing."""
        with self.assertLogs(
            "odoo.addons.message_center_compassion.models.field_to_json", "WARNING"
        ):
            self.assertEqual(self.spec.from_json("Weird"), {})
