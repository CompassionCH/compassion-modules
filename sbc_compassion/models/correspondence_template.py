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

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


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
    name = fields.Char()
    active = fields.Boolean(default=True)
    layout = fields.Selection('get_gmc_layouts', required=True)
    pattern_image = fields.Binary(required=True)
    template_attachment_id = fields.Many2one('ir.attachment')
    template_image = fields.Binary(
        compute='_compute_image', inverse='_set_image')
    page_width = fields.Integer(
        required=True, help='Width of the template in pixels')
    page_height = fields.Integer(
        required=True, help='Height of the template in pixels')
    bluesquare_x = fields.Integer(
        required=True,
        help='X Position of the upper-right corner of the bluesquare '
             'in pixels')
    bluesquare_y = fields.Integer(
        required=True,
        help='Y Position of the upper-right corner of the bluesquare '
             'in pixels')
    qrcode_x_min = fields.Integer(
        required=True,
        help='Minimum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_x_max = fields.Integer(
        required=True,
        help='Maximum X position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_min = fields.Integer(
        required=True,
        help='Minimum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    qrcode_y_max = fields.Integer(
        required=True,
        help='Maximum Y position of the area in which to look for the QR '
             'code inside the template (given in pixels)')
    pattern_x_min = fields.Integer(
        required=True,
        help='Minimum X position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_x_max = fields.Integer(
        required=True,
        help='Maximum X position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_y_min = fields.Integer(
        required=True,
        help='Minimum Y position of the area in which to look for the '
             'pattern inside the template (given in pixels)')
    pattern_y_max = fields.Integer(
        required=True,
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
        width = self.page_width
        height = self.page_height
        valid_coordinates = (
            self.bluesquare_x >= 0 and self.bluesquare_x <= width and
            self.bluesquare_y >= 0 and self.bluesquare_y <= height and
            self.qrcode_x_min >= 0 and self.qrcode_x_min < self.qrcode_x_max
            and self.qrcode_x_max <= width and
            self.qrcode_y_min >= 0 and self.qrcode_y_min < self.qrcode_y_max
            and self.qrcode_y_max <= height and
            self.pattern_x_min >= 0 and
            self.pattern_x_min < self.pattern_x_max and
            self.pattern_x_max <= width and
            self.pattern_y_min >= 0 and
            self.pattern_y_min < self.pattern_y_max and
            self.pattern_y_max <= height)
        if not valid_coordinates:
            raise ValidationError(_("Please give valid coordinates."))

    @api.depends('template_attachment_id')
    def _compute_image(self):
        self.template_image = self.template_attachment_id.datas

    def _set_image(self):
        if self.template_image:
            if self.template_attachment_id:
                self.template_attachment_id.datas = self.template_image
            else:
                attachment = self.env['ir.attachment'].create({
                    'name': self.name,
                    'res_model': self._name,
                    'datas': self.template_image,
                    'datas_fname': self.name,
                    'res_id': self.id
                })
                self.template_attachment_id = attachment.id

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_layout_names(self):
        return [name[0] for name in self.get_gmc_layouts]


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
        required=True,
        help='Minimum X position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    x_max = fields.Integer(
        required=True,
        help='Maximum X position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    y_min = fields.Integer(
        required=True,
        help='Minimum Y position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')
    y_max = fields.Integer(
        required=True,
        help='Maximum Y position of the area in which to look for the '
             'checkbox inside the template (given in pixels)')

    @api.constrains(
        'x_min', 'x_max', 'y_min', 'y_max')
    def verify_position(self):
        width = self.template_id.page_width
        height = self.template_id.page_height
        valid_coordinates = (
            self.x_min >= 0 and self.x_min < self.x_max and
            self.x_max <= width and
            self.y_min >= 0 and self.y_min < self.y_max and
            self.y_max <= height
        )
        if not valid_coordinates:
            raise ValidationError(_("Please give valid coordinates."))
