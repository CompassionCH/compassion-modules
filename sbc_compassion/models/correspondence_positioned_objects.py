##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class CorrespondencePositionedObject(models.Model):
    """This class represents any object that is positioned in a PDF. A
    positioned object is anything that is located with its left-highest and
    right-lowest point."""

    _name = "correspondence.positioned.object"
    _description = "Correspondence positioned object"

    name = fields.Char()
    x_min = fields.Float(
        help="Minimum X position of the object in millimeters", required=True
    )
    x_max = fields.Float(
        help="Maximum X position of the object in millimeters", required=True
    )
    y_min = fields.Float(
        help="Minimum Y position of the object in millimeters", required=True
    )
    y_max = fields.Float(
        help="Maximum Y position of the object in millimeters", required=True
    )

    def get_json_repr(self):
        """
        Utility to get the JSON representation of the text box which will
        be used by FPDF library to render the text box in a PDF.
        :return: list of values
        """
        self.ensure_one()
        return list(map(str, [self.x_min, self.y_min, self.x_max, self.y_max]))


class CorrespondenceTextBox(models.Model):
    _name = "correspondence.text.box"
    _inherit = "correspondence.positioned.object"
    _description = "Correspondence Text Box"

    text_line_height = fields.Float(help="Line height in millimeters", required=True)
    text_type = fields.Selection(
        [
            ("Original", "Original"),
            ("Translation", "Translation"),
        ]
    )

    def get_json_repr(self):
        """
        Utility to get the JSON representation of the text box which will
        be used by FPDF library to render the text box in a PDF.
        :return: list of values
        """
        self.ensure_one()
        res = super().get_json_repr()
        if self.text_type:
            res.append(self.text_type)
        res.append(str(self.text_line_height))
        return res
