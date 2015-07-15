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
import requests


class child_pictures(models.Model):
    """ Holds two pictures of a given child
        - Headshot
        - Fullshot
    """

    _name = 'compassion.child.pictures'
    _order = 'date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade')
    fullshot = fields.Binary(compute='set_pictures')
    headshot = fields.Binary(compute='set_pictures')
    date = fields.Date('Date of pictures')
    case_study_id = fields.Many2one(
        'compassion.child.property', 'Case study', readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    def set_pictures(self):
        """Get the picture given field_name (headshot or fullshot)"""
        attachment_obj = self.env['ir.attachment']
        attachments = attachment_obj.search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)])
        for data in attachments:
            if data.datas_fname == 'Fullshot.jpeg':
                self.fullshot = data.datas
            elif data.datas_fname == 'Headshot.jpeg':
                self.headshot = data.datas

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
        child = pictures.child_id

        # Retrieve Fullshot
        image_date = self._get_picture(
            child.id, child.code, pictures.id, 'Fullshot', dpi=300,
            width=1500, height=1200)
        # Retrieve Headshot
        image_date = image_date and self._get_picture(
            child.id, child.code, pictures.id)

        if not image_date:
            # We could not retrieve a picture, we cancel the creation
            pictures._unlink_related_attachment()
            pictures.unlink()
            return False

        # Find if same pictures already exist
        same_pictures = pictures._find_same_picture()
        if same_pictures:
            # Don't keep the new picture and return the previous one.
            pictures._unlink_related_attachment()
            pictures.unlink()
            same_pictures.write({'date': image_date})
            child.message_post(
                _('The picture was the same'), 'Picture update')
            pictures = same_pictures[0]
        else:
            pictures.write({'date': image_date})

        if not pictures.case_study_id:
            # Attach the picture to the last Case Study
            case_study = child.case_study_ids and child.case_study_ids[0]
            if case_study and not case_study.pictures_id:
                six_months = 180
                case_study_date = case_study.info_date
                case_study_date = datetime.strptime(case_study_date, DF)

                picture_date = pictures.date
                picture_date = datetime.strptime(picture_date, DF)

                date_diff = abs((case_study_date - picture_date).days)

                if (date_diff <= six_months or child.type == 'LDP'):
                    case_study.attach_pictures(pictures.id)
                    pictures.write({'case_study_id': case_study.id})

        return pictures

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _unlink_related_attachment(self):
        self.ensure_one()
        self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)]).unlink()

    def _find_same_picture(self):
        self.ensure_one()
        pics = self.search([('child_id', '=', self.child_id.id)])
        same_pics = pics.filtered(
            lambda record: record.fullshot == self.fullshot and
            record.headshot == self.headshot and record.id != self.id)
        return same_pics

    @api.model
    def _get_picture(self, child_id, child_code, attach_id, type='Headshot',
                     dpi=72, width=400, height=400, format='jpeg'):
        """ Gets a picture from Compassion webservice """
        url = self.env['compassion.child'].get_url(
            child_code, 'image/2015/03')
        url += '&Height=%s&Width=%s&DPI=%s&ImageFormat=%s&ImageType=%s' \
            % (height, width, dpi, format, type)
        r = requests.get(url)
        error = r.status_code != 200
        html_res = r.text
        json_data = dict()

        try:
            json_data = r.json()
        except:
            error = True
        if error:
            error_message = json_data.get('error', {'message': html_res})
            self.env['mail.thread'].with_context(
                thread_model='compassion.child').message_post(
                self.env.cr, self.env.user.id, child_id,
                error_message.get('message', 'Bad response'),
                _('Picture update error'), 'comment')
            return False

        _store_fname = type + '.' + format
        _image_date = json_data['imageDate'] or datetime.today().strftime(DF)

        self.env['ir.attachment'].create({
            'datas_fname': _store_fname,
            'res_model': self._name,
            'res_id': attach_id,
            'datas': json_data['image']['imageData'],
            'name': _store_fname})

        return _image_date
