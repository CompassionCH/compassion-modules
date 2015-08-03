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

from openerp import models, fields, api, exceptions, _
from openerp.tools.config import config


class compassion_country(models.Model):
    _name = 'compassion.country'

    description_en = fields.Text('English description')
    description_fr = fields.Text('French description')
    description_de = fields.Text('German description')
    description_it = fields.Text('Italian description')
    iso_code = fields.Char('ISO code', size=2, required=True)
    name = fields.Char('Name')
    name_en = fields.Char('English name', related='name')
    name_fr = fields.Char('French name')
    name_de = fields.Char('German name')
    name_it = fields.Char('Italian name')
    language = fields.Char('Official language')
    project_ids = fields.One2many(
        'compassion.project', 'country_id', 'Country projects')

    def update_informations(self):
        for country in self:
            url = self._get_url('iso', country.iso_code)
            r = requests.get(url)
            if not r.status_code/100 == 2:
                continue

            json_data = json.loads(r.text)
            values = self._get_val_from_json(json_data)
            country.write(values)
        return True

    @api.model
    def _get_val_from_json(self, json_data):
        values = dict()
        values['name'] = json_data['countryCommonName']
        values['description_en'] = json_data['countryDescription']
        values['language'] = json_data['officialLanguage']
        return values

    @api.model
    def _get_url(self, api_mess, api_value):
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise exceptions.Warning(
                'ConfigError', _('Missing compass_url or compass_api_key '
                                 'in conf file'))
        if url.endswith('/'):
            url = url[:-1]
        url += ('/ci/v1/countries/' + api_mess + '/' + api_value +
                '?api_key=' + api_key)
        return url
