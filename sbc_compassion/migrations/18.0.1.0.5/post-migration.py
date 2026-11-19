from odoo import SUPERUSER_ID
from odoo.api import Environment

# Reference text box (christmas page 1 box): a 39.5% x 52.2% box holds about
# 1100 characters, with 30 characters per line when rendered by wkhtmltopdf.
# Other boxes are scaled by their width and surface.
REFERENCE_WIDTH = 39.5
REFERENCE_HEIGHT = 52.2
REFERENCE_MAX_CHARS = 1100
REFERENCE_LINE_SIZE = 30


def migrate(cr, version):
    """
    Text boxes created by hand have no max_chars and line_size, so the text of
    the letters is never spread on several pages and overflows the template.
    Fill the missing values from the size of the box. The existing values are
    never modified.
    """
    env = Environment(cr, SUPERUSER_ID, {})
    text_boxes = env["correspondence.text.box"].search(
        [
            ("text_type", "!=", False),
            "|",
            ("max_chars", "=", 0),
            ("line_size", "=", 0),
        ]
    )
    for text_box in text_boxes:
        vals = {}
        if not text_box.max_chars:
            surface_ratio = (text_box.width * text_box.height) / (
                REFERENCE_WIDTH * REFERENCE_HEIGHT
            )
            vals["max_chars"] = int(REFERENCE_MAX_CHARS * surface_ratio)
        if not text_box.line_size:
            vals["line_size"] = max(
                1, round(REFERENCE_LINE_SIZE * text_box.width / REFERENCE_WIDTH)
            )
        text_box.write(vals)
