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
import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)

try:
    # import httplib
    import simplejson
except ImportError:
    _logger.warning("Please install httplib and simplejson")


class TestOnramp(common.HttpCase):
    """ Base class for all Onramp tests. """

    def setUp(self):
        # TODO Reactivate tests when new authentication is done
        # Add special controller for decoding a fake Oauth token
        super(TestOnramp, self).setUp()

        self.server_url = self.env['ir.config_parameter'].get_param(
            'web.base.url',
            default='http://localhost:8069'
        )
        api_client_secret = base64.b64encode("client:secret")
        self.rest_url = '{0}/onramp?token={1}'.format(
            self.server_url, api_client_secret)
        # params_post = 'grant_type=client_credentials&scope=read+write'
        # header_post = {
        #     "Authorization": "Basic " + api_client_secret,
        #     "Content-type": "application/x-www-form-urlencoded",
        #     "Content-Length": 46,
        #     "Expect": "100-continue",
        #     "Connection": "Keep-Alive",
        # }
        # conn = httplib.HTTPSConnection('api2.compassion.com')
        # conn.request("POST", "/pcore/connect/token", params_post,
        # header_post)
        # response = conn.getresponse()
        # data_token = simplejson.loads(response.read())
        # conn.close()

        # headers = [
        #     ('Content-type', 'application/json'),
        #     ('Authorization', '{token_type} {access_token}'.format(
        #         **data_token)),
        #     ("x-cim-MessageType", "http://schemas.ci.org/ci/services/"
        #         "communications/2015/09/SBCStructured"),
        #     ("x-cim-FromAddress", "CHTest"),
        #     ("x-cim-ToAddress", "CH"),
        # ]
        # self.opener.addheaders.extend(headers)

    def _send_post(self, vals):
        data = simplejson.dumps(vals)
        return self.url_open(self.rest_url, data)
