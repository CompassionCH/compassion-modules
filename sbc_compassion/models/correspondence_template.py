# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import tempfile
import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

from ..tools import patternrecognition as pr

_logger = logging.getLogger(__name__)

try:
    import numpy
    import cv2
except ImportError:
    _logger.warning('Please install numpy, and cv2 to use SBC module')


class Style:
    """ Defines a few colors for drawing on the result picture
    (names from wikipedia).
    The color order is BGR"""
    pattern_color_sq = (34, 139, 34)  # green (forest)
    pattern_color_pt = (0, 128, 0)  # green (html/css color)
    pattern_color_key = (0, 204, 239)  # yellow (munsell)
    qr_color = (168, 24, 0)  # blue (Pantone)
    lang_color = (0, 97, 232)  # Spanish orange
    # defines scaling for circles radius
    radius_scale = 120


class CorrespondenceTemplate(models.Model):
    """ This class defines a template used for Supporter Letters and holds
    all information relative to position of metadata in the Template, like for
    instance where the QR Code is supposed to be, where the language
    checkboxes will be found, where the pattern will be, etc...

    Template images should be in 300 DPI
    """
    _name = 'correspondence.template'
    _description = 'Correspondence template'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    layout = fields.Selection('get_gmc_layouts', required=True)
    pattern_image = fields.Binary(attachment=True)
    template_image = fields.Binary(attachment=True, help='Use 300 DPI images')
    page_width = fields.Integer(help='Width of the template in pixels')
    page_height = fields.Integer(help='Height of the template in pixels')
    qrcode_x_min = fields.Integer(
        help='Minimum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_x_max = fields.Integer(
        help='Maximum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_min = fields.Integer(
        help='Minimum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_max = fields.Integer(
        help='Maximum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    pattern_x_min = fields.Integer(
        help='Minimum X position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_x_max = fields.Integer(
        help='Maximum X position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_y_min = fields.Integer(
        help='Minimum Y position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_y_max = fields.Integer(
        help='Maximum Y position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    checkbox_ids = fields.One2many(
        'correspondence.lang.checkbox', 'template_id', copy=True)
    nber_keypoints = fields.Integer("Number of key points")
    usage_count = fields.Integer(
        compute='_compute_usage_count'
    )
    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Report for S2B generation',
        required=True,
        domain=[('model', '=', 'correspondence.s2b.generator')],
        default=lambda s: s.env.ref('sbc_compassion.report_s2b_letter'),
    )
    text_box_left_position = fields.Float(help='In millimeters')
    text_box_top_position = fields.Float(help='In millimeters')
    text_box_width = fields.Float(help='In millimeters')
    text_box_height = fields.Float(help='In millimeters')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    def get_gmc_layouts(self):
        """ Returns the layouts available to use with GMC. """
        return [
            ('CH-A-1S11-1', _('Layout 1')),
            ('CH-A-2S01-1', _('Layout 2')),
            ('CH-A-3S01-1', _('Layout 3')),
            ('CH-A-4S01-1', _('Layout 4')),
            ('CH-A-5S01-1', _('Layout 5')),
            ('CH-A-6S11-1', _('Layout 6'))]

    @api.constrains(
        'pattern_x_min', 'pattern_x_max',
        'pattern_y_min', 'pattern_y_max', 'page_width', 'page_height')
    def verify_position(self):
        """ Check that position of elements inside template are valid
        coordinates. """
        for tpl in self:
            if not _verify_template(tpl):
                raise ValidationError(_("Please give valid coordinates."))

    @api.multi
    def _compute_usage_count(self):
        for template in self:
            template.usage_count = self.env['correspondence'].search_count([
                ('template_id', '=', template.id)
            ])

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        template = super(CorrespondenceTemplate, self).create(vals)
        template._compute_template_data()
        return template

    @api.multi
    def write(self, vals):
        super(CorrespondenceTemplate, self).write(vals)
        if 'template_image' in vals or 'pattern_image' in vals:
            self._compute_template_data()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_layout_names(self):
        return [name[0] for name in self.get_gmc_layouts]

    def get_pattern_area(self):
        """ Returns a numpy array of floats with the pattern area coordinates
            relative to the page size.
            [x_min, x_max, y_min, y_max]
        """
        area = numpy.array([
            self.pattern_x_min, self.pattern_x_max, self.pattern_y_min,
            self.pattern_y_max], float)
        area[:2] = area[:2]/float(self.page_width)
        area[2:] = area[2:]/float(self.page_height)
        return area

    def get_template_size(self, resize_factor=1.0):
        """ Returns the width and height of the template in a numpy array. """
        wh = numpy.array([self.page_width, self.page_height])
        wh *= resize_factor
        return wh

    def _compute_template_data(self):
        config_obj = self.env['ir.config_parameter']
        for template in self.filtered('template_image'):
            template_cv_image = template._get_cv2_image()
            template.page_height, template.page_width = \
                template_cv_image.shape[:2]
            template.qrcode_x_min = template.page_width * float(
                config_obj.get_param('qrcode_x_min'))
            template.qrcode_x_max = template.page_width * float(
                config_obj.get_param('qrcode_x_max'))
            template.qrcode_y_min = template.page_height * \
                float(config_obj.get_param('qrcode_y_min'))
            template.qrcode_y_max = template.page_height * \
                float(config_obj.get_param('qrcode_y_max'))
            if template.pattern_image:
                # pattern detection
                res = pr.patternRecognition(
                    template_cv_image, template.pattern_image,
                    template.get_pattern_area())
                if res is None:
                    raise UserError(
                        _("The pattern could not be detected in given "
                          "template image."))
                else:
                    pattern_keypoints = res[0]

                template.nber_keypoints = pattern_keypoints.shape[0]

    def _get_cv2_image(self):
        self.ensure_one()
        with tempfile.NamedTemporaryFile(suffix='.png') as template_file:
            template_file.write(base64.b64decode(self.template_image))
            template_file.flush()
            template_cv_image = cv2.imread(template_file.name)
        return template_cv_image


class CorrespondenceLanguageCheckbox(models.Model):
    """ This class represents a checkbox that can be present in a template
    and can be ticked by the supporter to select the language in which the
    letter is written. It gives the position of the checkbox inside a template
    in order to find it and verify if it is ticked or not. """

    _name = 'correspondence.lang.checkbox'

    template_id = fields.Many2one(
        'correspondence.template', required=True,
        ondelete='cascade')
    language_id = fields.Many2one('res.lang.compassion')
    x_min = fields.Integer(
        help='Minimum X position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    x_max = fields.Integer(
        help='Maximum X position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    y_min = fields.Integer(
        help='Minimum Y position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    y_max = fields.Integer(
        help='Maximum Y position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')

    @api.constrains(
        'x_min', 'x_max', 'y_min', 'y_max')
    def verify_position(self):
        for checkbox in self:
            width = checkbox.template_id.page_width
            height = checkbox.template_id.page_height
            valid_coordinates = (
                0 <= checkbox.x_min <= checkbox.x_max <= width and
                0 <= checkbox.y_min <= checkbox.y_max <= height
            )
            if not valid_coordinates:
                raise ValidationError(_("Please give valid coordinates."))


def _verify_template(tpl):
    """
    Test each position if a CorrespondenceTemplate in order to
    see if 0 < min < max < size where size is the size of the page.
    """
    width = tpl.page_width
    height = tpl.page_height
    if tpl.template_image and tpl.pattern_image:
        valid_coordinates = (
            0 <= tpl.pattern_x_min < tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min < tpl.pattern_y_max <= height)
    else:
        valid_coordinates = (
            0 <= tpl.pattern_x_min <= tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min <= tpl.pattern_y_max <= height)
    return valid_coordinates


class CorrespondenceDefaultTemplate(models.Model):

    _name = 'correspondence.default.template'

    name = fields.Char(required=True)

    default_template_id = fields.Many2one(
        'correspondence.template', 'S2B Template', required=True)
