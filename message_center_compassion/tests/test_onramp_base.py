# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import urllib2
import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)

try:
    import httplib
    import simplejson
except ImportError:
    _logger.warning("Please install httplib and simplejson")


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
        header_post = {
            "Authorization": "Basic " + api_client_secret,
            "Content-type": "application/x-www-form-urlencoded",
            "Content-Length": 46,
            "Expect": "100-continue",
            "Connection": "Keep-Alive",
        }
        conn = httplib.HTTPSConnection('api2.compassion.com')
        conn.request("POST", "/core/connect/token", params_post, header_post)
        response = conn.getresponse()
        data_token = simplejson.loads(response.read())
        conn.close()

        self.headers = {
            'Content-type': 'application/json',
            'Authorization': '{token_type} {access_token}'.format(
                **data_token),
            "x-cim-MessageType": "http://schemas.ci.org/ci/services/"
            "communications/2015/09/SBCStructured",
            "x-cim-FromAddress": "CHTest",
            "x-cim-ToAddress": "CH",
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
