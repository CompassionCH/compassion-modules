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
import cv2

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError, Warning
from wand.image import Image

from ..tools import patternrecognition as pr
from ..tools import bluecornerfinder as bcf


class Style:
    """ Defines a few colors for drawing on the result picture
    (names from wikipedia).
    The color order is BGR"""
    pattern_color_sq = (34, 139, 34)  # green (forest)
    pattern_color_pt = (0, 128, 0)  # green (html/css color)
    pattern_color_key = (0, 204, 239)  # yellow (munsell)
    bluesquare_color = (51, 2, 196)  # red NCS
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

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    layout = fields.Selection('get_gmc_layouts', required=True)
    pattern_image = fields.Binary()
    template_image = fields.Binary(
        compute='_compute_image', inverse='_set_image',
        help='Use 300 DPI images')
    detection_result = fields.Binary(
        compute='_compute_detection')
    page_width = fields.Integer(
        help='Width of the template in pixels')
    page_height = fields.Integer(
        help='Height of the template in pixels')
    bluesquare_x = fields.Integer(
        compute='_compute_template_keypoints', store=True,
        help='X Position of the upper-right corner of the blue square '
             'in pixels')
    bluesquare_y = fields.Integer(
        compute='_compute_template_keypoints', store=True,
        help='Y Position of the upper-right corner of the blue square '
             'in pixels')
    qrcode_x_min = fields.Integer(
        compute="_onchange_template_image",
        help='Minimum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_x_max = fields.Integer(
        compute="_onchange_template_image",
        help='Maximum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_min = fields.Integer(
        compute="_onchange_template_image",
        help='Minimum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_max = fields.Integer(
        compute="_onchange_template_image",
        help='Maximum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    pattern_center_x = fields.Float(
        compute="_compute_template_keypoints", store=True,
        help='X coordinate of the center of the pattern. '
        'Used to detect the orientation of the pattern in the image')
    pattern_center_y = fields.Float(
        compute="_compute_template_keypoints", store=True,
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
        'correspondence.lang.checkbox', 'template_id',
        default=lambda self: self._get_default_checkboxes(), copy=True)
    nber_keypoints = fields.Integer(
        "Number of key points", compute="_compute_template_keypoints",
        store=True)

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
        'bluesquare_x', 'bluesquare_y', 'pattern_x_min', 'pattern_x_max',
        'pattern_y_min', 'pattern_y_max', 'page_width', 'page_height')
    def verify_position(self):
        """ Check that position of elements inside template are valid
        coordinates. """
        for tpl in self:
            if not _verify_template(tpl):
                raise ValidationError(_("Please give valid coordinates."))

    def _compute_image(self):
        for template in self:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', template.id)])
            if attachment:
                template.template_image = attachment.datas

    def _set_image(self):
        if self.template_image:
            datas = base64.b64decode(self.template_image)
            ftype = magic.from_buffer(datas, True)
            if not ('jpg' in ftype or 'jpeg' in ftype or 'png' in ftype):
                raise Warning(
                    _("Unsupported format"),
                    _("Please only use jpg or png files."))
            # Be sure image is in 300 DPI
            with Image(blob=datas, resolution=300) as img:
                datas = base64.b64encode(img.make_blob())
            attachment_obj = self.env['ir.attachment']
            attachment = attachment_obj.search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id)])
            if attachment:
                attachment.datas = datas
            else:
                attachment = attachment_obj.create({
                    'name': self.name,
                    'datas': datas,
                    'datas_fname': self.name,
                    'res_model': self._name,
                    'res_id': self.id
                })
            # Trigger again computation of keypoints
            self._compute_template_keypoints()

    @api.onchange('template_image')
    def _onchange_template_image(self):
        for template in self:
            # compute image size and QR code position
            template._compute_img_constant()

    def _compute_img_constant(self):
        """ Compute the position of the QR code and the size of the image

        :returns: Image
        :rtype: np.array

        """
        data = self.with_context(
            bin_size=False).template_image or self.template_image
        if not data:
            return None

        with tempfile.NamedTemporaryFile(suffix='.png') as template_file:
            template_file.write(base64.b64decode(data))
            template_file.flush()
            template_cv_image = cv2.imread(template_file.name)
        self.page_height, self.page_width = template_cv_image.shape[:2]
        config_obj = self.env['ir.config_parameter']
        self.qrcode_x_min = self.page_width * float(
            config_obj.get_param('qrcode_x_min'))
        self.qrcode_x_max = self.page_width * float(
            config_obj.get_param('qrcode_x_max'))
        self.qrcode_y_min = self.page_height * \
            float(config_obj.get_param('qrcode_y_min'))
        self.qrcode_y_max = self.page_height * \
            float(config_obj.get_param('qrcode_y_max'))

        return template_cv_image

    @api.depends('pattern_image')
    def _compute_template_keypoints(self):
        """ This method computes all key points that can be automatically
        detected (blue square and pattern_center)
        """
        for template in self:
            if (template.template_image and template.pattern_image):
                # compute image size and QR code position
                img = template._compute_img_constant()
                if img is not None:
                    # pattern detection
                    pattern_keypoints = pr.patternRecognition(
                        img, template.pattern_image,
                        template.get_pattern_area())
                    if pattern_keypoints is None:
                        raise Warning(
                            _("Pattern not found"),
                            _("The pattern could not be detected in given "
                              "template image."))
                    template.nber_keypoints = pattern_keypoints.shape[0]
                    # find center of the pattern
                    pattern_center = pr.keyPointCenter(pattern_keypoints)
                    template.pattern_center_x = pattern_center[0]
                    template.pattern_center_y = pattern_center[1]
                    # blue corner detection
                    bluecorner = bcf.BlueCornerFinder(
                        img).getIndices()
                    template.bluesquare_x = bluecorner[0]
                    template.bluesquare_y = bluecorner[1]

    @api.multi
    def _compute_detection(self):
        for template in self:
            if (template.pattern_image and template.template_image and
                    _verify_template(template)):
                img = template._compute_img_constant()
                if img is None:
                    pass

                # computation before any modifications
                pattern_keypoints = pr.patternRecognition(
                    img, template.with_context(bin_size=False).pattern_image,
                    template.get_pattern_area())
                # no reason behind it, just need a scaling
                radius = template.page_width/Style.radius_scale
                # blue square
                img.itemset((self.bluesquare_y, self.bluesquare_x, 0),
                            Style.bluesquare_color[0])
                img.itemset((self.bluesquare_y, self.bluesquare_x, 1),
                            Style.bluesquare_color[1])
                img.itemset((self.bluesquare_y, self.bluesquare_x, 2),
                            Style.bluesquare_color[2])
                cv2.circle(img, (self.bluesquare_x, self.bluesquare_y),
                           radius, Style.bluesquare_color)
                config = self.env['ir.config_parameter']
                bc_x_min = int(
                    float(config.get_param('bluecorner_x_min')) *
                    template.page_width)
                bc_y_max = int(
                    float(config.get_param('bluecorner_y_max')) *
                    template.page_height)
                cv2.rectangle(img,
                              (bc_x_min, 0), (template.page_width, bc_y_max),
                              Style.bluesquare_color)

                # QR code
                cv2.rectangle(img,
                              (template.qrcode_x_min, template.qrcode_y_min),
                              (template.qrcode_x_max, template.qrcode_y_max),
                              Style.qr_color)
                # Pattern
                # box
                pattern_center = (int(self.pattern_center_y),
                                  int(self.pattern_center_x))
                cv2.rectangle(img,
                              (template.pattern_x_min, template.pattern_y_min),
                              (template.pattern_x_max, template.pattern_y_max),
                              Style.pattern_color_sq)
                # center
                img.itemset((pattern_center[0], pattern_center[1], 0),
                            Style.pattern_color_pt[0])
                img.itemset((pattern_center[0], pattern_center[1], 1),
                            Style.pattern_color_pt[1])
                img.itemset((pattern_center[0], pattern_center[1], 2),
                            Style.pattern_color_pt[2])
                cv2.circle(img, pattern_center[::-1], radius,
                           Style.pattern_color_pt)
                # key points
                for key in pattern_keypoints:
                    cv2.line(img, (int(key[0]), int(key[1])),
                             pattern_center[::-1],
                             Style.pattern_color_key)

                # languages
                for check in template.checkbox_ids:
                    cv2.rectangle(img,
                                  (check.x_min, check.y_min),
                                  (check.x_max, check.y_max),
                                  Style.lang_color)
                    pos = (int(check.x_min + check.x_max)/2,
                           int(check.y_min + check.y_max)/2)
                    if check.language_id.code_iso is not False:
                        cv2.putText(img, check.language_id.code_iso, pos,
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    Style.lang_color)
                with tempfile.NamedTemporaryFile(
                        suffix='.png') as template_file:
                    cv2.imwrite(template_file.name, img)
                    template.detection_result = base64.b64encode(
                        template_file.read())

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
        """ Returns the coordinates of the blue square upper-right corner
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
            0 <= tpl.bluesquare_x <= width and
            0 <= tpl.bluesquare_y <= height and
            0 <= tpl.pattern_x_min < tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min < tpl.pattern_y_max <= height)
    else:
        valid_coordinates = (
            0 <= tpl.bluesquare_x <= width and
            0 <= tpl.bluesquare_y <= height and
            0 <= tpl.pattern_x_min <= tpl.pattern_x_max <= width and
            0 <= tpl.pattern_y_min <= tpl.pattern_y_max <= height)
    return valid_coordinates
