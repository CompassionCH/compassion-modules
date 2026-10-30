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
        # Size of the christmas letter box
        self.text_box = self.env["correspondence.text.box"].create(
            {
                "name": "Test box",
                "x_min": 7.14,
                "y_min": 18.52,
                "width": 39.52,
                "height": 52.19,
                "text_line_height": 24,
                "text_type": "Original",
            }
        )

    def _spread(self, text):
        """Simulates the pagination: each page keeps what fits in the box."""
        pages = []
        for _i in range(1000):
            fits, overflow = self.text_box.split_text(text)
            pages.append(fits)
            if not overflow:
                return pages
            text = overflow
        self.fail("The text is never fully spread on pages")

    def test_short_text_is_unchanged(self):
        text = "Dear Olivier,\nMerry Christmas!\n\nYour sponsor"
        self.assertEqual(self.text_box.split_text(text), (text, ""))

    def test_spread_normal_text(self):
        words = ("lorem ipsum dolor " * 300).split()
        pages = self._spread(" ".join(words))
        self.assertGreater(len(pages), 2)
        spread_words = [w for page in pages for w in page.split() if w != "..."]
        self.assertEqual(spread_words, words)

    def test_line_breaks_take_space(self):
        sentence = "Merry Christmas to you and your family! "
        fits, _overflow = self.text_box.split_text(sentence * 60)
        fits_with_breaks, _overflow = self.text_box.split_text((sentence + "\n\n") * 60)
        self.assertLess(len(fits_with_breaks), len(fits))

    def test_spread_word_longer_than_box(self):
        url = "https://example.com/" + "".join(str(i % 10) for i in range(1500))
        pages = self._spread(f"Look at {url} please")
        self.assertGreater(len(pages), 1)
        # Apart from the words around it, the URL must only be split between pages
        # and never contain a space.
        url_parts = []
        for page in pages:
            parts = [
                w for w in page.split() if w not in ("Look", "at", "please", "...")
            ]
            self.assertLessEqual(len(parts), 1, f"Space inserted in URL: {page}")
            url_parts.extend(parts)
        self.assertEqual("".join(url_parts), url)

    def test_nothing_fits_keeps_text(self):
        self.text_box.height = 1
        self.assertEqual(self.text_box.split_text("word"), ("word", ""))
