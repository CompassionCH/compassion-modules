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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

from datetime import date, datetime
import requests


class child_pictures(orm.Model):
    """ Holds two pictures of a given child
        - Headshot
        - Fullshot
    """

    _name = 'compassion.child.pictures'
    _order = 'date desc'

    def get_picture(self, cr, uid, ids, field_name, args, context=None):
        """Get the picture given field_name (headshot or fullshot)"""
        attachment_obj = self.pool.get('ir.attachment')
        res = dict()
        for id in ids:
            attachment_ids = attachment_obj.search(
                cr, uid, [('res_model', '=', self._name),
                          ('res_id', '=', id),
                          ('datas_fname', 'ilike', field_name)],
                limit=1, context=context)
            if not attachment_ids:
                res[id] = None
                continue

            attachment = attachment_obj.browse(cr, uid, attachment_ids[0],
                                               context)
            res[id] = attachment.datas
        return res

    _columns = {
        'child_id': fields.many2one('compassion.child', _('Child'),
                                    required=True, ondelete='cascade'),
        'fullshot': fields.function(get_picture, type='binary',
                                    string=_('Fullshot')),
        'headshot': fields.function(get_picture, type='binary',
                                    string=_('Headshot')),
        'date': fields.date(_('Date of pictures')),
        'case_study_id': fields.many2one(
            'compassion.child.property', _('Case study'), readonly=True)
    }

    _defaults = {
        'date': date.today().strftime(DF),
    }

    def create(self, cr, uid, vals, context=None):
        """ Fetch new pictures from GMC webservice when creating
        a new Pictures object. Check if picture is the same as the previous
        and attach the pictures to the last case study.
        """
        if context is None:
            context = dict()
        res_id = super(child_pictures, self).create(cr, uid, vals, context)

        child = self.pool.get('compassion.child').browse(
            cr, uid, vals['child_id'], context)
        # Retrieve Fullshot
        success = self._get_picture(
            cr, uid, child.id, child.code, res_id, context, 'Fullshot',
            dpi=300, width=1500, height=1200)
        # Retrieve Headshot
        success = success and self._get_picture(cr, uid, child.id, child.code,
                                                res_id, context)
        child_picture = self.browse(cr, uid, res_id, context)
        if not success:
            # We could not retrieve a picture, we cancel the creation
            self._unlink_related_attachment(cr, uid, child_picture.id, context)
            self.unlink(cr, uid, res_id, context)
            return False

        # Find if same pictures already exist
        same_picture_ids = self._find_same_picture(
            cr, uid, child.id,
            child_picture.fullshot, child_picture.headshot,
            context)
        same_picture_ids.remove(child_picture.id)

        if same_picture_ids:
            # Don't keep the new picture and return the previous one.
            self._unlink_related_attachment(cr, uid, child_picture.id, context)
            self.unlink(cr, uid, res_id, context)
            self.write(
                cr, uid, same_picture_ids,
                {'date': context['image_date']}, context)
            self.pool.get('mail.thread').message_post(
                cr, uid, child.id,
                _('The picture was the same'), 'Picture update',
                context={'thread_model': 'compassion.child'})
            res_id = same_picture_ids[0]
            child_picture = self.browse(cr, uid, res_id, context)
        else:
            child_picture.write({'date': context['image_date']})

        if not child_picture.case_study_id:
            # Attach the picture to the last Case Study
            case_study = child.case_study_ids and child.case_study_ids[0]
            if case_study and not case_study.pictures_id:
                six_months = 180
                case_study_date = case_study.info_date
                case_study_date = datetime.strptime(case_study_date, DF)

                picture_date = child_picture.date
                picture_date = datetime.strptime(picture_date, DF)

                date_diff = abs((case_study_date - picture_date).days)

                if (date_diff <= six_months or child.type == 'LDP'):
                    case_study.attach_pictures(res_id)
                    child_picture.write({'case_study_id': case_study.id})

        return res_id

    def _unlink_related_attachment(self, cr, uid, res_id, context=None):
        attachment_obj = self.pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(
            cr, uid,
            [('res_model', '=', 'compassion.child.pictures'),
                ('res_id', '=', res_id)],
            context=context)
        attachment_obj.unlink(cr, uid, attachment_ids, context)

    def _find_same_picture(
            self, cr, uid, child_id, fullshot, headshot, context):
        pict_ids = self.search(
            cr, uid, [('child_id', '=', child_id)], context=context)
        same_pict_ids = list()
        for picture in self.browse(cr, uid, pict_ids, context):
            if (picture.fullshot == fullshot and
               picture.headshot == headshot):
                    same_pict_ids.append(picture.id)
        return same_pict_ids

    def _get_picture(self, cr, uid, child_id, child_code, attach_id, context,
                     type='Headshot', dpi=72, width=400, height=400,
                     format='jpeg'):
        ''' Gets a picture from Compassion webservice '''
        url = self.pool.get('compassion.child').get_url(
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
            self.pool.get('mail.thread').message_post(
                cr, uid, child_id,
                error_message.get('message', 'Bad response'),
                _('Picture update error'), 'comment',
                context={'thread_model': 'compassion.child'})
            return False

        attachment_obj = self.pool.get('ir.attachment')
        context['store_fname'] = type + '.' + format
        context['image_date'] = json_data['imageDate'] or date.today()
        return attachment_obj.create(cr, uid, {
            'datas_fname': type + '.' + format,
            'res_model': self._name,
            'res_id': attach_id,
            'datas': json_data['image']['imageData'],
            'name': type + '.' + format}, context)
