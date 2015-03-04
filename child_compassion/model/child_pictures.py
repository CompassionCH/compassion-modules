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

from datetime import date
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
    }

    _defaults = {
        'date': date.today().strftime(DF),
    }

    def create(self, cr, uid, vals, context=None):
        """ Fetch new pictures from GMC webservice when creating
        a new Pictures object.
        """
        res_id = super(child_pictures, self).create(cr, uid, vals, context)
        child = self.pool.get('compassion.child').browse(
            cr, uid, vals['child_id'], context)
        # Retrieve Fullshot
        success = self._get_picture(
            cr, uid, child.id, child.code, res_id, 'Fullshot',
            dpi=300, width=1500, height=1200, context=context)
        # Retrieve Headshot
        success = success and self._get_picture(cr, uid, child.id, child.code,
                                                res_id, context=context)
        child_picture = self.browse(
            cr, uid, res_id, context)
        if not success:
            # We could not retrieve a picture, we cancel the creation
            self._unlink_related_attachment(cr, uid, child_picture.id, context)
            self.unlink(cr, uid, res_id, context)
            return False

        same_picture_ids = self._find_same_picture(
            cr, uid, child.id,
            child_picture.fullshot, child_picture.headshot,
            context)
        same_picture_ids.remove(child_picture.id)

        if same_picture_ids:
            self._unlink_related_attachment(cr, uid, child_picture.id, context)
            self.unlink(cr, uid, res_id, context)
            self.write(
                cr, uid, same_picture_ids,
                {'date': date.today()}, context)
            return False
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
            if picture.fullshot == fullshot:
                if picture.headshot == headshot:
                    same_pict_ids.append(picture.id)
        return same_pict_ids

    def _get_picture(self, cr, uid, child_id, child_code, attach_id,
                     type='Headshot', dpi=72, width=400, height=400,
                     format='jpeg', context=None):
        ''' Gets a picture from Compassion webservice '''
        url = self.pool.get('compassion.child').get_url(child_code, 'image')
        url += '&Height=%s&Width=%s&DPI=%s&ImageFormat=%s&ImageType=%s' \
            % (height, width, dpi, format, type)
        r = requests.get(url)
        json_data = r.json()
        if not r.status_code/100 == 2:
            self.pool.get('mail.thread').message_post(
                cr, uid, child_id,
                json_data['error']['message'],
                _('Picture update error'), 'comment',
                context={'thread_model': 'compassion.child'})
            return False

        attachment_obj = self.pool.get('ir.attachment')
        if not context:
            context = dict()
        context['store_fname'] = type + '.' + format

        return attachment_obj.create(cr, uid, {
            'datas_fname': type + '.' + format,
            'res_model': self._name,
            'res_id': attach_id,
            'datas': json_data['image']['imageData'],
            'name': type + '.' + format}, context)
