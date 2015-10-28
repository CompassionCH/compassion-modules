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
        required=True, help='Width of the template in pixels')
    page_height = fields.Integer(
        required=True, help='Height of the template in pixels')
    bluesquare_x = fields.Integer(
        compute='_compute_template_keypoints', store=True,
        help='X Position of the upper-right corner of the bluesquare '
             'in pixels')
    bluesquare_y = fields.Integer(
        compute='_compute_template_keypoints', store=True,
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
        compute='_compute_template_keypoints', store=True,
        help='X coordinate of the center of the pattern. '
        'Used to detect the orientation of the pattern in the image')
    pattern_center_y = fields.Float(
        compute='_compute_template_keypoints', store=True,
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
            ('L1', _('Layout 1')),
            ('L2', _('Layout 2')),
            ('L3', _('Layout 3')),
            ('L4', _('Layout 4')),
            ('L5', _('Layout 5')),
            ('L6', _('Layout 6'))]

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
        for template in self:
            width = template.page_width
            height = template.page_height
            valid_coordinates = (
                template.bluesquare_x >= 0 and template.bluesquare_x <= width
                and template.bluesquare_y >= 0 and
                template.bluesquare_y <= height and template.qrcode_x_min >= 0
                and template.qrcode_x_min <= template.qrcode_x_max
                and template.qrcode_x_max <= width and
                template.qrcode_y_min >= 0 and
                template.qrcode_y_min <= template.qrcode_y_max and
                template.qrcode_y_max <= height and
                template.pattern_x_min >= 0 and
                template.pattern_x_min <= template.pattern_x_max and
                template.pattern_x_max <= width and
                template.pattern_y_min >= 0 and
                template.pattern_y_min <= template.pattern_y_max and
                template.pattern_y_max <= height)
            if not valid_coordinates:
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

    @api.depends('template_attachment_id',
                 'pattern_image')
    def _compute_template_keypoints(self):
        """ This method computes all keypoints that can be automatically
        detected (bluesquare and pattern_center)
        """
        for template in self:
            if template.template_image and template.pattern_image:
                with tempfile.NamedTemporaryFile() as template_file:
                    template_file.write(base64.b64decode(
                        template.template_image))
                    template_file.flush()
                    # Find the pattern inside the template image
                    pattern_keypoints = pr.patternRecognition(
                        template_file.name, template.pattern_image,
                        template.get_pattern_area())
                    if pattern_keypoints is None:
                        raise Warning(
                            _("Pattern not found"),
                            _("The pattern could not be detected in given "
                              "template image."))
                    pattern_center = pr.keyPointCenter(pattern_keypoints)
                    template.pattern_center_x = pattern_center[0]
                    template.pattern_center_y = pattern_center[1]

                    bluecorner = bcf.BlueCornerFinder(
                        template_file.name).getIndices()
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
                checkbox.x_min >= 0 and checkbox.x_min < checkbox.x_max and
                checkbox.x_max <= width and
                checkbox.y_min >= 0 and checkbox.y_min < checkbox.y_max and
                checkbox.y_max <= height
            )
            if not valid_coordinates:
                raise ValidationError(_("Please give valid coordinates."))
