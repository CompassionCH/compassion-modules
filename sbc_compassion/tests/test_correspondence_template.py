from odoo.tests import TransactionCase


class TestCorrespondenceTemplate(TransactionCase):
    def test_copy_template_copies_text_boxes_limits(self):
        text_box = self.env["correspondence.text.box"].create(
            {
                "name": "Test box",
                "x_min": 7,
                "y_min": 18,
                "width": 40,
                "height": 52,
                "text_line_height": 24,
                "text_type": "Original",
                "max_chars": 1100,
                "line_size": 30,
            }
        )
        template = self.env["correspondence.template"].create(
            {
                "name": "Test template",
                "page_ids": [
                    (0, 0, {"page_index": 1, "text_box_ids": [(6, 0, text_box.ids)]})
                ],
            }
        )
        copy = template.copy()
        copied_box = copy.page_ids.text_box_ids
        self.assertEqual(len(copied_box), 1)
        self.assertNotEqual(copied_box, text_box)
        self.assertEqual(copied_box.max_chars, 1100)
        self.assertEqual(copied_box.line_size, 30)
        self.assertEqual(template.page_ids.text_box_ids, text_box)
