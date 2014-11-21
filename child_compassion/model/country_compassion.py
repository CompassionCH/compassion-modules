# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import requests
import json

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config


class compassion_country(orm.Model):
    _name = 'compassion.country'

    _columns = {
        'description_en': fields.text(_('English description')),
        'description_fr': fields.text(_('French description')),
        'description_de': fields.text(_('German description')),
        'description_it': fields.text(_('Italian description')),
        'iso_code': fields.char(_('ISO code'), size=2, required=True),
        'name': fields.char(_('Name')),
        'name_en': fields.related('name', type='char', string='Name'),
        'name_fr': fields.char(_('Name')),
        'name_de': fields.char(_('Name')),
        'name_it': fields.char(_('Name')),
        'language': fields.char(_('Official language')),
        'project_ids': fields.one2many(
            'compassion.project', 'country_id', _('Country projects')),
    }

    def update_informations(self, cr, uid, ids, context=None):
        countries = self.browse(cr, uid, ids, context=context)
        for country in countries:
            url = self._get_url('iso', country.iso_code)
            r = requests.get(url)
            if not r.status_code/100 == 2:
                continue

            json_data = json.loads(r.text)
            values = self._get_val_from_json(cr, uid, json_data, context)
            self.write(cr, uid, [country.id], values, context=context)

        return

    def _get_val_from_json(self, cr, uid, json_data, context=None):
        values = {}

        values['name'] = json_data['countryCommonName']
        values['description_en'] = json_data['countryDescription']
        values['language'] = json_data['officialLanguage']
        return values

    def _get_url(self, api_mess, api_value):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += ('/ci/v1/countries/' + api_mess + '/' + api_value +
                '?api_key=' + api_key)
        return url
