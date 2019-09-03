# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CorrespondencePositionedObject(models.Model):
    """ This class represents any object that is positioned in a PDF. A
    positioned object is anything that is located with its left-highest and
    right-lowest point. """
    _name = 'correspondence.positioned.object'

    x_min = fields.Float(help='Minimum X position of the object')
    x_max = fields.Float(help='Maximum X position of the object')
    y_min = fields.Float(help='Minimum Y position of the object')
    y_max = fields.Float(help='Maximum Y position of the object')


class CorrespondenceTextBox(models.Model):
    _name = 'correspondence.text.box'
    _inherit = 'correspondence.positioned.object'

    text_line_height = fields.Float()
    text_type = fields.Char(string='Type')


class CorrespondenceLanguageCheckbox(models.Model):
    """ This class represents a checkbox that can be present in a template
    and can be ticked by the supporter to select the language in which the
    letter is written. It gives the position of the checkbox inside a template
    in order to find it and verify if it is ticked or not.
    The object s  """

    _name = 'correspondence.lang.checkbox'
    _inherit = 'correspondence.positioned.object'

    template_id = fields.Many2one(
        'correspondence.template', required=True,
        ondelete='cascade')
    language_id = fields.Many2one('res.lang.compassion')

    @api.constrains('x_min', 'x_max', 'y_min', 'y_max')
    def verify_position(self):
        for checkbox in self:
            width = checkbox.template_id.page_width
            height = checkbox.template_id.page_height
            valid_coordinates = (
                0 <= checkbox.x_min <= checkbox.x_max <= width and
                0 <= checkbox.y_min <= checkbox.y_max <= height)
            if not valid_coordinates:
                raise ValidationError(_("Please give valid coordinates."))
