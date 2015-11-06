# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import numpy
import base64
import tempfile
import magic
from cv2 import imread

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError, Warning

from ..tools import patternrecognition as pr
from ..tools import bluecornerfinder as bcf


class CorrespondenceTemplate(models.Model):
    """ This class defines a template used for Supporter Letters and holds
    all information relative to position of metadata in the Template, like for
    instance where the QR Code is supposed to be, where the language
    checkboxes will be found, where the pattern will be, etc...
    """

    _name = 'sponsorship.correspondence.template'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    layout = fields.Selection('get_gmc_layouts', required=True)
    pattern_image = fields.Binary()
    template_attachment_id = fields.Many2one('ir.attachment', copy=False)
    template_image = fields.Binary(
        compute='_compute_image', inverse='_set_image')
    detection_result = fields.Binary(
        compute='_compute_detection')
    page_width = fields.Integer(
        readonly=True,
        help='Width of the template in pixels')
    page_height = fields.Integer(
        readonly=True,
        help='Height of the template in pixels')
    bluesquare_x = fields.Integer(
        readonly=True,
        help='X Position of the upper-right corner of the bluesquare '
             'in pixels')
    bluesquare_y = fields.Integer(
        readonly=True,
        help='Y Position of the upper-right corner of the bluesquare '
             'in pixels')
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
    pattern_center_x = fields.Float(
        readonly=True,
        help='X coordinate of the center of the pattern. '
        'Used to detect the orientation of the pattern in the image')
    pattern_center_y = fields.Float(
        readonly=True,
        help='Y coordinate of the center of the pattern. '
        'Used to detect the orientation of the pattern in the image')
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
        'sponsorship.correspondence.lang.checkbox', 'template_id',
        default=lambda self: self._get_default_checkboxes())

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
            ('CH-A-6S01-1', _('Layout 6'))]

    def _get_default_checkboxes(self):
        return [
            (0, False, {'language_id': self.env.ref(
                'sbc_compassion.lang_compassion_french').id}),
            (0, False, {'language_id': self.env.ref(
                'sbc_compassion.lang_compassion_german').id}),
            (0, False, {'language_id': self.env.ref(
                'sbc_compassion.lang_compassion_italian').id}),
            (0, False, {'language_id': self.env.ref(
                'sbc_compassion.lang_compassion_english').id}),
            (0, False, {'language_id': self.env.ref(
                'sbc_compassion.lang_compassion_spanish').id}),
            (0, False, {'language_id': False}),
        ]

    @api.constrains(
        'bluesquare_x', 'bluesquare_y', 'qrcode_x_min', 'qrcode_x_max',
        'qrcode_y_min', 'qrcode_y_max', 'pattern_x_min', 'pattern_x_max',
        'pattern_y_min', 'pattern_y_max')
    def verify_position(self):
        """ Check that position of elements inside template are valid
        coordinates. """
        for tpl in self:
            if not _verify_template_created(tpl):
                raise ValidationError(_("Please give valid coordinates."))

    @api.depends('template_attachment_id')
    def _compute_image(self):
        for template in self:
            template.template_image = template.template_attachment_id.datas

    def _set_image(self):
        if self.template_image:
            ftype = magic.from_buffer(
                base64.b64decode(self.template_image), True)
            if not ('jpg' in ftype or 'jpeg' in ftype or 'png' in ftype):
                raise Warning(
                    _("Unsupported format"),
                    _("Please only use jpg or png files."))
            if self.template_attachment_id:
                self.template_attachment_id.datas = self.template_image
                # Trigger again computation of keypoints
                self._compute_template_keypoints()
            else:
                attachment = self.env['ir.attachment'].create({
                    'name': self.name,
                    'res_model': self._name,
                    'datas': self.template_image,
                    'datas_fname': self.name,
                    'res_id': self.id
                })
                self.template_attachment_id = attachment.id

    @api.depends('template_image')
    def _compute_detection(self):
        for template in self:
            original_image = template.template_image
            # TODO : add detection results to original_image
            template.detection_result = original_image

    @api.onchange('template_attachment_id',
                  'pattern_image', 'template_image')
    def _compute_template_keypoints(self):
        """ This method computes all keypoints that can be automatically
        detected (bluesquare and pattern_center)
        """
        for template in self:
            if (template.template_image and template.pattern_image):
                with tempfile.NamedTemporaryFile() as template_file:
                    template_file.write(base64.b64decode(
                        template.template_image))
                    template_file.flush()
                    # Find the pattern inside the template image
                    img = imread(template_file.name)
                    template.page_height, template.page_width = img.shape[:2]
                    # verify that datas are given for the detection
                    if _verify_template_created(template, equal=False):
                        # pattern detection
                        pattern_keypoints = pr.patternRecognition(
                            img, template.pattern_image,
                            template.get_pattern_area())
                        if pattern_keypoints is None:
                            raise Warning(
                                _("Pattern not found"),
                                _("The pattern could not be detected in given "
                                "template image."))
                        # find center of the pattern
                        pattern_center = pr.keyPointCenter(pattern_keypoints)
                        template.pattern_center_x = pattern_center[0]
                        template.pattern_center_y = pattern_center[1]
                        # blue corner detection
                        bluecorner = bcf.BlueCornerFinder(
                            img).getIndices()
                        template.bluesquare_x = bluecorner[0]
                        template.bluesquare_y = bluecorner[1]

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

    def get_bluesquare_area(self):
        """ Returns the coordinates of the bluesquare upper-right corner
            [x, y]
        """
        return numpy.array([self.bluesquare_x, self.bluesquare_y])

    def get_template_size(self):
        """ Returns the width and height of the template in a numpy array. """
        return numpy.array([self.page_width, self.page_height])

    def get_pattern_center(self):
        """ Returns the coordinates of the pattern center. """
        return numpy.array([self.pattern_center_x, self.pattern_center_y])


class CorrespondenceLanguageCheckbox(models.Model):
    """ This class represents a checkbox that can be present in a template
    and can be ticked by the supporter to select the lang in which the letter
    is written. It gives the position of the checkbox inside a template in
    order to find it and verify if it is ticked or not. """

    _name = 'sponsorship.correspondence.lang.checkbox'

    template_id = fields.Many2one(
        'sponsorship.correspondence.template', required=True,
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


def _verify_template_created(tpl, equal=True):
    """
    Test each position if a CorrespondenceTemplate in order to
    see if 0 < min < max < size where size is the size of the page.
    equal is used in order to define if the equality is accepted.
    In case of True all the operator will be <=, in case of False
    only the comparison with the min and max will be changed
    """
    width = tpl.page_width
    height = tpl.page_height
    if equal:
        valid_coordinates = (
            0 <= tpl.bluesquare_x <= width and
            0 <= tpl.bluesquare_y <= height and
            0 <= tpl.qrcode_x_min <= tpl.qrcode_x_max <= width and
            0 <= tpl.qrcode_y_min <= tpl.qrcode_y_max <= height and
            0 <= tpl.pattern_x_min <= tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min <= tpl.pattern_y_max <= height)
    else:
        valid_coordinates = (
            0 <= tpl.bluesquare_x <= width and
            0 <= tpl.bluesquare_y <= height and
            0 <= tpl.qrcode_x_min < tpl.qrcode_x_max <= width and
            0 <= tpl.qrcode_y_min < tpl.qrcode_y_max <= height and
            0 <= tpl.pattern_x_min < tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min < tpl.pattern_y_max <= height)
    return valid_coordinates
