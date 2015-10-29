# -*- coding: utf-8 -*-
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import base64
import urllib2
import httplib
import simplejson
import pdb

from openerp.tests import common


class TestOnramp(common.HttpCase):
    """ Base class for all Onramp tests. """

    def setUp(self):
        super(TestOnramp, self).setUp()

        self.server_url = self.env['ir.config_parameter'].get_param(
            'web.base.url',
            default='http://localhost:8069'
        )
        api_client_secret = base64.b64encode("client:secret")
        self.rest_url = '{0}/onramp?secret={1}'.format(
            self.server_url, api_client_secret)
        params_post = 'grant_type=client_credentials&scope=read+write'
        header_post = {"Authorization": "Basic " + api_client_secret,
                       "Content-type": "application/x-www-form-urlencoded",
                       "Content-Length": 46,
                       "Expect": "100-continue",
                       "Connection": "Keep-Alive"}
        conn = httplib.HTTPSConnection('api2.compassion.com')
        conn.request("POST", "/core/connect/token", params_post, header_post)
        response = conn.getresponse()
        data_token = simplejson.loads(response.read())
        conn.close()

        self.headers = {
            'Content-type': 'application/json',
            'Authorization': '{token_type} {access_token}'.format(**data_token)
        }

    def test_no_token(self):
        """ Check we have an access denied if token is not provided
        """
        del self.headers['Authorization']
        with self.assertRaises(urllib2.HTTPError) as e:
            self._send_post({'nothing': 'nothing'})
        self.assertEqual(e.exception.code, 401)
        self.assertEqual(e.exception.msg, 'UNAUTHORIZED')

    def test_bad_token(self):
        """ Check we have an access denied if token is not valid
        """
        pdb.set_trace()
        self.headers['Authorization'] = 'Bearer notarealtoken'
        with self.assertRaises(urllib2.HTTPError) as e:
            self._send_post({'nothing': 'nothing'})
        self.assertEqual(e.exception.code, 401)
        self.assertEqual(e.exception.msg, 'UNAUTHORIZED')

    def test_body_no_json(self):
        req = urllib2.Request(self.rest_url, "This is not json", self.headers)
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen(req)

    def _send_post(self, vals):
        data = simplejson.dumps(vals)
        req = urllib2.Request(self.rest_url, data, self.headers)
        return urllib2.urlopen(req)
