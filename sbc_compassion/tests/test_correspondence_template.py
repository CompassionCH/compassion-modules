from odoo.tests import TransactionCase


class TestCorrespondenceTemplate(TransactionCase):
    def test_copy_template_shares_text_boxes(self):
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
        # Templates with the same layout share their text boxes
        self.assertEqual(copy.page_ids.text_box_ids, text_box)
        self.assertEqual(copy.page_ids.text_box_ids.max_chars, 1100)
        self.assertEqual(copy.page_ids.text_box_ids.line_size, 30)


class TestTextSpreading(TransactionCase):
    def setUp(self):
        super().setUp()
        self.paragraph = self.env["correspondence.paragraph"]

    def _spread(self, text, max_chars=100, line_size=30):
        """Simulates the pagination: each page keeps what fits in the box."""
        pages = []
        for _i in range(1000):
            fits, overflow = self.paragraph._finalize_text(
                *self.paragraph._split_text(text, max_chars, line_size)
            )
            pages.append(fits)
            if not overflow:
                return pages
            text = overflow
        self.fail("The text is never fully spread on pages")

    def test_spread_normal_text(self):
        pages = self._spread("lorem ipsum dolor " * 30)
        self.assertGreater(len(pages), 1)
        self.assertTrue(all(len(page) <= 110 for page in pages))

    def test_spread_word_longer_than_box(self):
        url = "https://example.com/" + "a" * 5000
        pages = self._spread(f"Look at {url} please")
        self.assertGreater(len(pages), 1)
        text = "".join("".join(page.replace("...", "").split()) for page in pages)
        self.assertEqual(text, f"Lookat{url}please")

    def test_nothing_fits_keeps_text(self):
        fits, overflow = self.paragraph._finalize_text([], ["word"])
        self.assertEqual((fits, overflow), ("word", ""))
