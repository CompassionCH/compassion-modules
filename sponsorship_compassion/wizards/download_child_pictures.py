##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import urllib.request
import urllib.error
from io import BytesIO
from odoo import models, api, fields
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
    height = fields.Integer()
    width = fields.Integer()
    download_data = fields.Binary(readonly=True)
    preview = fields.Binary(compute='_compute_preview')
    information = fields.Text(readonly=True)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def get_file_name(self):
        return fields.Date.context_today(self) + '_child_pictures.zip'

    @api.multi
    def get_picture_url(self, raw_url, pic_type, width, height):
        if pic_type.lower() == 'headshot':
            cloudinary = "g_face,c_thumb,h_" + str(height) + ",w_" + str(
                width)
        elif pic_type.lower() == 'fullshot':
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        image_split = raw_url.split('/')
        ind = image_split.index('media.ci.org')
        image_split[ind + 1] = cloudinary
        url = "/".join(image_split)
        return url

    @api.multi
    def get_pictures(self):
        """ Create the zip archive from the selected letters. """
        children = self._get_children()

        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_data:
            found = 0

            for child in children.filtered('image_url'):
                child_code = child.local_id
                url = self.get_picture_url(raw_url=child.image_url,
                                           pic_type=self.type,
                                           height=self.height,
                                           width=self.width)
                try:
                    data = base64.encodestring(
                        urllib.request.urlopen(url).read())
                except urllib.error.URLError:
                    # Not good, the url doesn't lead to an image
                    logger.error('Image cannot be fetched: ' + str(
                        url))
                    continue

                format = url.split('.')[-1]
                sponsor_ref = child.sponsor_ref
                fname = sponsor_ref + '_' + child_code + '.' + format

                zip_data.writestr(fname, base64.b64decode(data))
                found += 1

        zip_buffer.seek(0)
        if found:
            self.download_data = base64.b64encode(zip_buffer.read())

        self.information = 'Zip file contains ' + str(found) + ' ' \
                                                               'pictures.\n\n'
        self._check_picture_availability()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'context': self.env.context,
            'target': 'new',
            }

    _height_change = 0
    _width_change = 0

    @api.onchange('type')  # if these fields are changed,
    # call method
    def _type_onchange(self):
        if self.type == 'headshot':
            self.height = 400
            self.width = 300
        else:
            self.height = 1200
            self.width = 800
        self._height_change += 1
        self._width_change += 1
        self._compute_preview()

    @api.onchange('height')  # if these fields are changed,
    # call method
    def _height_onchange(self):
        if self._height_change == 0:
            if self.type == 'fullshot':
                self.width = round(self.height * 800 // 1200)
                self._width_change += 1
            self._compute_preview()
        else:
            self._height_change -= 1

    @api.onchange('width')  # if these fields are changed,
    # call method
    def _width_onchange(self):
        if self._width_change == 0:
            if self.type == 'fullshot':
                self.height = round(self.width * 1200 // 800)
                self._height_change += 1
            self._compute_preview()
        else:
            self._width_change -= 1

    @api.multi
    def _compute_preview(self):
        children = self._get_children()

        for child in children.filtered('image_url'):
            url = child.image_url
            try:
                url = self.get_picture_url(url, self.type, self.width,
                                           self.height)
                self.preview = base64.encodestring(
                    urllib.request.urlopen(url[0]).read())
                break
            except:
                logger.error('Image cannot be fetched : ' + url)

    @api.multi
    def _check_picture_availability(self):
        children = self._get_children()

        # Search children having a 'image_url' returning False
        children_with_no_url = children.filtered(
            lambda c: not c.image_url
            )
        # If there is some, we will print their corresponding childe_code
        if children_with_no_url:
            child_codes = children_with_no_url.mapped('local_id')
            self.information += 'No image url for child(ren):\n\t' + \
                                '\n\t'.join(child_codes) + '\n\n'

        # Now we want children having an invalid 'image_url'.
        # To find them, we have to try to open their url and catch exceptions.
        children_with_invalid_url = []
        for child in children.filtered('image_url'):
            url = self.get_picture_url(
                raw_url=child.image_url,
                pic_type='fullshot', height=1, width=1
                )
            try:
                urllib.request.urlopen(url)
            except urllib.error.URLError:
                # Not good, the url doesn't lead to an image
                children_with_invalid_url += [child.local_id]
        if children_with_invalid_url:
            self.information += 'Invalid image url for child(ren):\n\t' + \
                                '\n\t'.join(children_with_invalid_url)

    @api.multi
    def _get_children(self):
        context = self.env.context['active_model']
        if context == 'res.partner':
            partners = self.env[context].browse(
                self.env.context['active_ids'])
            contracts = self.env['recurring.contract'].search([
                '|',
                ('correspondent_id', 'in', partners.ids),
                ('partner_id', 'in', partners.ids),
                ('type', 'in', ['S', 'SC']),
                ('state', '!=', 'cancelled')
            ])
        elif context == 'recurring.contract':
            contracts = self.env[context].browse(
                self.env.context['active_ids'])

        elif context == 'compassion.child':
            childrens = self.env[context].browse(
                self.env.context['active_ids'])
            contracts = self.env['recurring.contract'].search([
                ('child_id', 'in', childrens.ids),
                ('type', 'in', ['S', 'SC']),
                ('state', '!=', 'cancelled')
            ])

        children = contracts.mapped('child_id')
        return children
