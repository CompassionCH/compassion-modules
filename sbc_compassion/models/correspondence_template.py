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
import subprocess
import json
import os.path

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
    template_image2 = fields.Binary(attachment=True, help='Use 300 DPI images')
    template_image3 = fields.Binary(attachment=True, help='Use 300 DPI images')
    template_image4 = fields.Binary(attachment=True, help='Use 300 DPI images')
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
    # checkbox_ids = fields.One2many(
    #     'correspondence.lang.checkbox', 'template_id', copy=True)
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
    header_box = fields.Many2one('correspondence.text.box', string="Header")
    header_box2 = fields.Many2one('correspondence.text.box', string="Header 2")
    header_box3 = fields.Many2one('correspondence.text.box', string="Header 3")
    header_box4 = fields.Many2one('correspondence.text.box', string="Header 4")
    text_boxes = fields.Many2many('correspondence.text.box', 'text_boxes_rel',
                                  string='Text boxes')
    text_boxes2 = fields.Many2many('correspondence.text.box',
                                   'text_boxes_rel2', string='Text boxes 2')
    text_boxes3 = fields.Many2many('correspondence.text.box',
                                   'text_boxes_rel3', string='Text boxes 3')
    text_boxes4 = fields.Many2many('correspondence.text.box',
                                   'text_boxes_rel4', string='Text boxes 4')
    image_boxes = fields.Many2many('correspondence.positioned.object',
                                   'image_boxes_rel', string='Image boxes')
    image_boxes2 = fields.Many2many('correspondence.positioned.object',
                                    'image_boxes_rel2', string='Image boxes 2')
    image_boxes3 = fields.Many2many('correspondence.positioned.object',
                                    'image_boxes_rel3', string='Image boxes 3')
    image_boxes4 = fields.Many2many('correspondence.positioned.object',
                                    'image_boxes_rel4', string='Image boxes 4')
    # text_box_left_position = fields.Float(help='In millimeters')
    # text_box_top_position = fields.Float(help='In millimeters')
    # text_box_width = fields.Float(help='In millimeters')
    # text_box_height = fields.Float(help='In millimeters')

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


#######################################################################
#                              EXAMPLE                                #
#######################################################################
class TestGeneratePDF(models.Model):
    """
    Test class for generating a PDF
    """
    _name = 'test.generate.pdf'

    def generate_pdf(self, pdf_name, model_id, header, text, image_list):
        """
        Generate a pdf file
        This function is nearly as generic as it should be to be implemented
        directly to generate PDF for any template, text and image
        We save every text to a temp txt file to avoid having to escape all
        characters that could potentially be problematic
        :param pdf_name: path and name of the pdf file to write on
        :param model_id: id of the template
        :param header: dict of text for the headers to display {template page
            number (between 1 and 4: text}
        :param text: a dict of {type of text ('O' or 'T'): text}
        :param image_list: a list of image to display
        """
        pdf_file = open(pdf_name, "w")

        temp_img = []
        temp_header = []
        temp_text = []

        model = self.env['correspondence.template'].search([
            ('id', '=', model_id)])

        t_images = [model['template_image'], model['template_image2'],
                    model['template_image3'], model['template_image4']]
        h_data = [model['header_box'], model['header_box2'],
                  model['header_box3'], model['header_box4']]
        t_data = [model.mapped('text_boxes'), model.mapped('text_boxes2'),
                  model.mapped('text_boxes3'), model.mapped('text_boxes4')]
        i_data = [model.mapped('image_boxes'), model.mapped('image_boxes2'),
                  model.mapped('image_boxes3'), model.mapped('image_boxes4')]

        template_list = []
        for i in range(0, len(t_images)):
            if t_images[i]:
                temp_img.append(tempfile.NamedTemporaryFile(prefix='img_',
                                                            suffix='.jpg'))
                temp_img[-1].write(base64.b64decode(t_images[i]))
                temp_img[-1].flush()
                header_list = []
                if h_data[i] and (i+1) in header:
                    temp_header.append(tempfile.NamedTemporaryFile(
                        prefix='header_', suffix='.txt'))
                    temp_header[-1].write(header[i+1])
                    temp_header[-1].flush()
                    header_list = [temp_header[-1].name,
                                   str(h_data[i]['x_min']),
                                   str(h_data[i]['y_min']),
                                   str(h_data[i]['x_max']),
                                   str(h_data[i]['y_max']),
                                   str(h_data[i]['text_line_height'])]
                text_list = []
                for b in t_data[i]:
                    text_list.append([str(b['x_min']), str(b['y_min']),
                                      str(b['x_max']), str(b['y_max']),
                                      b['text_type'],
                                      str(b['text_line_height'])])
                image_list = []
                for b in i_data[i]:
                    image_list.append([str(b['x_min']), str(b['y_min']),
                                       str(b['x_max']), str(b['y_max'])])
                template_list.append([temp_img[-1].name, header_list,
                                      text_list, image_list])
            else:
                break

        text_list = []
        for t_type, txt in text.iteritems():
            temp_text.append(tempfile.NamedTemporaryFile(prefix=t_type + '_',
                                                         suffix='.txt'))
            temp_text[-1].write(txt)
            temp_text[-1].flush()
            text_list.append([temp_text[-1].name, t_type])

        generated_json = \
            {
                'images': image_list,
                'templates': template_list,
                'texts': text_list
            }

        json_val = json.dumps(generated_json).replace(' ', '')

        std_err_file = open(self.path_to('stderr.txt'), "w")

        proc = subprocess.Popen(['php', self.path_to('pdf.php'), json_val],
                                stdout=pdf_file, stderr=std_err_file)
        proc.communicate()

        for img in temp_img:
            img.close()

        for h in temp_header:
            h.close()

        for t in temp_text:
            t.close()

        std_err_file.close()

        return pdf_file.name

    def generate_pdf_test(self, pdf_name):
        txt_original = open(self.path_to('20k_c1.txt', 'static'), "r")
        txt_translated = open(self.path_to('20k_c2.txt', 'static'), "r")
        model_id = self.env['correspondence.template'].search([
            ('name', '=', 'Postman Test')])[0].id
        image_list = [self.path_to('b.png', 'static'), self.path_to(
            'c.png', 'static'), self.path_to('d.png', 'static')]
        header = {1: "Just a test\nOn multiple lines\nEven three"}
        text = {
            'O': txt_original.read(),
            'T': txt_translated.read()
        }
        txt_original.close()
        txt_translated.close()
        pdf_file = self.generate_pdf(self.path_to(pdf_name+'.pdf'), model_id,
                                     header, text, image_list)
        return pdf_file

    # path of the FPDF folder
    _absolute_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'FPDF/')

    # create path to the subfolder of FPDF
    def path_to(self, filename, folder=''):
        if folder == '':
            return os.path.join(self._absolute_path, filename)
        return os.path.join(self._absolute_path, folder + "/" + filename)
