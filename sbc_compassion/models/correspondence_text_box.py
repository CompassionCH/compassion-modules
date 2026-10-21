##############################################################################
#
#    Copyright (C) 2019-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Théo Nikles <theo.nikles@gmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models

# wkhtmltopdf renders the px line heights about 25% taller than what the
# max_chars and height of the boxes were designed for.
WKHTMLTOPDF_LINE_HEIGHT_SCALE = 0.8


class CorrespondenceTextBox(models.Model):
    _name = "correspondence.text.box"
    _description = "Correspondence Text Box"

    name = fields.Char()
    x_min = fields.Float(
        "Left position (%)",
        help="Left position of the object in percents (of the page)",
        required=True,
    )
    y_min = fields.Float(
        "Top position (%)",
        help="Top position of the object in percents (of the page)",
        required=True,
    )
    width = fields.Float(
        "Width (%)",
        help="Width of the object in percents (of the page size)",
        required=True,
    )
    height = fields.Float(
        "Height (%)",
        help="Height of the object in percents (of the page size)",
        required=True,
    )
    text_line_height = fields.Float(help="Line height in pixels", required=True)
    line_size = fields.Integer(
        help="Number of characters allowed per line. This will be used to compute "
        "how many characters a line break count as."
    )
    max_chars = fields.Integer(
        help="Maximum number of characters allowed in the box. If the text exceeds "
        "this limit, it will be moved into the next box of the template."
    )

    text_type = fields.Selection(
        [
            ("Original", "Original"),
            ("Translation", "Translation"),
        ]
    )
    css_style = fields.Char(compute="_compute_css_style")

    def _compute_css_style(self):
        """
        Get the overlay style for the given box, used on the Qweb-Report.
        """
        for text_box in self:
            line_height = text_box.text_line_height * WKHTMLTOPDF_LINE_HEIGHT_SCALE
            text_box.css_style = f"""
                position: absolute;
                top: {text_box.y_min}%;
                left: {text_box.x_min}%;
                width: {text_box.width}%;
                height: {text_box.height}%;
                line-height: {line_height}px;
            """
