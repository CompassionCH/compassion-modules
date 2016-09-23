# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import urllib2
from io import BytesIO
from openerp import models, api, fields
from zipfile import ZipFile
import logging

logger = logging.getLogger(__name__)


class DownloadChildPictures(models.TransientModel):
    """
    Utility to select multiple letters and download the attachments
    as a zip archive.
    """

    _name = 'child.pictures.download.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    fname = fields.Char(default=lambda s: s.get_file_name())
    type = fields.Selection([
        ('headshot', 'Headshot'),
        ('fullshot', 'Fullshot')
    ], default='headshot')
    #dpi = fields.Integer()
    height = fields.Integer()
    width = fields.Integer()
    download_data = fields.Binary(readonly=True)
    preview = fields.Binary(compute='_load_preview')

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def get_file_name(self):
        return fields.Date.context_today(self) + '_child_pictures.zip'

    @api.one
    def _get_picture_url(self, raw_url, type, width, height):
        if (type.lower() == 'headshot'):
            cloudinary = "g_face,c_thumb,h_" + str(height) + ",w_" + str(
                width)
        elif (type.lower() == 'fullshot'):
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        image_split = (raw_url).split('/')
        ind = image_split.index('upload')
        image_split[ind + 1] = cloudinary
        url = "/".join(image_split)
        return url



    @api.multi
    def get_pictures(self):
        """ Create the zip archive from the selected letters. """
        partners = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        contracts = self.env['recurring.contract'].search([
            '|',
            ('correspondant_id', 'in', partners.ids),
            ('partner_id', 'in', partners.ids),
            ('type', 'in', ['S', 'SC']),
            ('state', '=', 'active')
        ])
        children = contracts.mapped('child_id')

        pictures = self.env['compassion.child.pictures'].search([(
            'child_id', 'in', children.ids)])

        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_data:
            found = False
            #for child in children.filtered('image_url'):
            for picture in pictures:
                '''the "or True" have to be removed once we find a way to get
                 the pictures back from compassion.child.picture directly in
                  binary'''
                if self._customized() or True:
                    url = self._get_picture_url(raw_url=picture.image_url,
                        type=self.type, height=self.height, width=self.width)
                    url = url[0]
                    try:
                        data = base64.encodestring(
                            urllib2.urlopen(url).read())
                    except:
                        logger.error('Image cannot be fetched :' + str(url))
                        continue


                format = url.split('.')[-1]

                child = contracts.search([('child_id.id',
                    '=', picture.child_id.id), ('is_active', '=', True)])
                childCode = child.child_code
                childSponsor_idRef = child.partner_id.ref

                fname = childSponsor_idRef+'_'+childCode+'.'+format

                zip_data.writestr(fname, base64.b64decode(data))
                found = True
        zip_buffer.seek(0)
        self.download_data = found and base64.b64encode(zip_buffer.read())
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'context': self.env.context,
            'target': 'new',
        }


    '''
    @api.multi
    def get_pictures(self):
        """ Create the zip archive from the selected letters. """
        partners = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        children = self.env['recurring.contract'].search([
            '|',
            ('correspondant_id', 'in', partners.ids),
            ('partner_id', 'in', partners.ids),
            ('type', 'in', ['S', 'SC']),
            ('state', '=', 'active')
        ]).mapped('child_id')
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_data:
            found = False
            custom = self.dpi or self.height
            for child in children:
                if not custom:
                    pic = getattr(child.pictures_ids[0], self.type)
                else:
                    pic = self.env['compassion.child.pictures']._get_picture(
                        child.id, child.code, False, self.type, self.dpi,
                        height=self.height)
                if pic:
                    fname = child.sponsor_id.ref + '_' + child.code + '.jpg'
                    zip_data.writestr(fname, base64.b64decode(pic))
                    found = True
        zip_buffer.seek(0)
        self.download_data = found and base64.b64encode(zip_buffer.read())
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'context': self.env.context,
            'target': 'new',
        }
    '''

    _custom_invisible = 1
    @api.multi
    def enable_custom(self):
        self._custom_invisible = 1 - self._custom_invisible

    _height_change = 0
    _width_change = 0
    @api.onchange('type') # if these fields are changed,
    # call method
    def _type_onchange(self):
        if self.type == 'headshot':
            self.height = 400
            self.width = 300
        else:
            self.height = 1200
            self.width = 800
        self._height_change+=1
        self._width_change+=1
        self._load_preview()


    @api.onchange('height')  # if these fields are changed,
    # call method
    def _height_onchange(self):
        if self._height_change == 0:
            if self.type == 'fullshot':
                self.width = round(self.height * 800 / 1200)
                self._width_change += 1
            else:
                self._load_preview()
        else:
            self._height_change -= 1

    @api.onchange('width')  # if these fields are changed,
    # call method
    def _width_onchange(self):
        if self._width_change == 0:
            if self.type == 'fullshot':
                self.height = round(self.width * 1200 / 800)
                self._height_change += 1
            else:
                self._load_preview()
        else:
            self._width_change -= 1


    @api.multi
    def _load_preview(self):
        if self.type == 'fullshot':
            self.preview = False
            return

        partners = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])

        children = self.env['recurring.contract'].search([
            '|',
            ('correspondant_id', 'in', partners.ids),
            ('partner_id', 'in', partners.ids),
            ('type', 'in', ['S', 'SC']),
            ('state', '=', 'active')
        ]).mapped('child_id')

        for child in children.filtered('image_url'):
            url = child.image_url
            try:
                url = self._get_picture_url(url, 'headshot', self.width,
                                            self.height)
                self.preview = base64.encodestring(
                    urllib2.urlopen(url[0]).read())
                break
            except:
                logger.error('Image cannot be fetched : ' + url)

    def _customized(self):
        if self.type == 'fullshot':
            return not (self.width == 800 and self.height == 1200)
        else:
            return not (self.width == 300 and self.height == 400)
