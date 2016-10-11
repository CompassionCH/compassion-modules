# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

import logging
import base64
import urllib2

logger = logging.getLogger(__name__)


class child_pictures(models.Model):
    """ Holds two pictures of a given child
        - Headshot
        - Fullshot
    """

    _name = 'compassion.child.pictures'
    _order = 'date desc, id desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade')
    fullshot = fields.Binary(compute='set_pictures')
    headshot = fields.Binary(compute='set_pictures')
    image_url = fields.Char()
    date = fields.Date('Date of pictures', default=fields.Date.today)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    def set_pictures(self, typeshot='Headshot'):
        """Get the picture given field_name (headshot or fullshot)"""
        attachment_obj = self.env['ir.attachment']

        # We search related images, and sort them by date of creation
        # from newest to oldest
        attachments = attachment_obj.search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)],
            order='create_date desc')

        # We recover the newest Fullshot and Headshots
        for rec in attachments:
            if rec.datas_fname.split('.')[0] == 'Headshot':
                self.headshot = rec.datas
                break

        for rec in attachments:
            if rec.datas_fname.split('.')[0] == 'Fullshot':
                self.fullshot = rec.datas
                break

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Fetch new pictures from GMC webservice when creating
        a new Pictures object. Check if picture is the same as the previous
        and attach the pictures to the last case study.
        """
        pictures = super(child_pictures, self).create(vals)

        # Retrieve Headshot
        image_date = pictures._get_picture('Headshot', width=300, height=400)

        # Retrieve Fullshot
        image_date = image_date and pictures._get_picture('Fullshot',
                                                          width=800,
                                                          height=1200)

        if not image_date:
            # We could not retrieve a picture, we cancel the creation
            pictures._unlink_related_attachment()
            pictures.unlink()
            return False

        # Find if same pictures already exist
        same_pictures = pictures._find_same_picture()
        same_url = pictures._find_same_picture_by_url()
        if same_pictures or same_url:
            # Don't keep the new picture and return the previous one.
            pictures.child_id.message_post(
                _('The picture was the same'), 'Picture update')
            pictures._unlink_related_attachment()
            pictures.unlink()
            same_pictures.write({'date': image_date})
            pictures = same_pictures[0]
        else:
            pictures.write({'date': image_date})

        return pictures

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    def _unlink_related_attachment(self):
        self.ensure_one()
        self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)]).unlink()

    @api.multi
    def _find_same_picture_by_url(self):
        self.ensure_one()
        same_url = self.search([
            ('child_id', '=', self.child_id.id),
            ('image_url', '=', self.image_url),
            ('id', '!=', self.id)
        ])
        return same_url

    @api.multi
    def _find_same_picture(self):
        self.ensure_one()
        pics = self.search([('child_id', '=', self.child_id.id)])
        same_pics = pics.filtered(
            lambda record:
            record.fullshot == self.fullshot and
            record.headshot == self.headshot and
            record.id != self.id)

        return same_pics

    @api.multi
    def _get_picture(self, type='Headshot', width=300, height=400):
        """ Gets a picture from Compassion webservice """
        attach_id = self.id
        if (type.lower() == 'headshot'):
            cloudinary = "g_face,c_thumb,h_" + str(height) + ",w_" + str(
                width)
        elif (type.lower() == 'fullshot'):
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        _image_date = False
        for picture in self.filtered('image_url'):
            image_split = picture.image_url.split('/')
            ind = image_split.index('upload')
            image_split[ind + 1] = cloudinary
            url = "/".join(image_split)
            try:
                data = base64.encodestring(urllib2.urlopen(url).read())
            except:
                logger.error('Image cannot be fetched : ' + url)
                continue

            # recover the extension of the file (should be 'jpg')
            extension = url.split('.')[-1]
            # name of the file (typically 'Fullshot.jpg' or 'Headshot.jpg'
            _store_fname = type + '.' + extension

            _image_date = datetime.now().strftime(DF)

            if not attach_id:
                return data

            picture.env['ir.attachment'].create({
                'datas_fname': _store_fname,
                'res_model': picture._name,
                'res_id': attach_id,
                'datas': data,
                'name': _store_fname})
        return _image_date
