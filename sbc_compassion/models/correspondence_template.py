# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
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
    import magic
    import cv2
    from wand.image import Image
except ImportError:
    _logger.warning('Please install numpy, magic, cv2 and wand to use SBC '
                    'module')


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

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    layout = fields.Selection('get_gmc_layouts', required=True)
    pattern_image = fields.Binary()
    template_image = fields.Binary(
        compute='_compute_image', inverse='_set_image',
        help='Use 300 DPI images')  # resolution
    detection_result = fields.Binary(
        compute='_compute_detection')
    page_width = fields.Integer(
        help='Width of the template in pixels')
    page_height = fields.Integer(
        help='Height of the template in pixels')
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

    def _get_default_checkboxes(self):
        return [
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_french').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_german').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_italian').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_english').id}),
            (0, False, {'language_id': self.env.ref(
                'child_switzerland.lang_compassion_spanish').id}),
            (0, False, {'language_id': False}),
        ]

    @api.constrains(
        'pattern_x_min', 'pattern_x_max',
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
                raise UserError(
                    _("Please only use jpg or png files."))
            # Be sure image is in 300 DPI
            with Image(blob=datas, resolution=300) as img:  # resolution
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
        detected
        """
        for template in self:
            if template.template_image and template.pattern_image:
                # compute image size and QR code position
                img = template._compute_img_constant()
                if img is not None:
                    # pattern detection
                    res = pr.patternRecognition(
                        img, template.pattern_image,
                        template.get_pattern_area())
                    if res is None:
                        raise UserError(
                            _("The pattern could not be detected in given "
                              "template image."))
                    else:
                        pattern_keypoints = res[0]

                    template.nber_keypoints = pattern_keypoints.shape[0]

    @api.multi
    def _compute_detection(self):
        for template in self:
            if template.pattern_image and template.template_image:
                img = template._compute_img_constant()
                if img is None:
                    pass

                # QR code
                cv2.rectangle(img,
                              (template.qrcode_x_min, template.qrcode_y_min),
                              (template.qrcode_x_max, template.qrcode_y_max),
                              Style.qr_color)

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

    @api.multi
    def _compute_usage_count(self):
        for template in self:
            template.usage_count = self.env['correspondence'].search_count([
                ('template_id', '=', template.id)
            ])

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
