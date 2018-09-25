# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import jwt
from odoo.tests.common import HttpCase


class TestMobileAppHttp(HttpCase):

    def setUp(self):
        super(TestMobileAppHttp, self).setUp()
        self.root_url = '/mobile-app-api/'
        # Add JSON type in request headers
        self.opener.addheaders.append(('Content-Type', 'application/json'))
        # Add authentication for Oauth2
        payload = {
            'iss': 'https://esther.ci.org',
            'client_id': 'admin'
        }
        token = jwt.encode(payload, 'secret')
        self.opener.addheaders.append(('Authorization', 'Bearer ' + token))

    def test_missing_parameters(self):
        url = self.root_url + 'correspondence/get_letters'
        response = self.url_open(url)
        body_str = response.read()
        error_message = json.loads(body_str)['error']['message']
        self.assertEqual(error_message, u"Required parameter supgrpid")

    def test_for_valid_requests(self):
        url = self.root_url + 'compassion.child/sponsor_children?userid=25'
        response = self.url_open(url)

        self.assertEqual(response.code, 200)

    def test_with_invalid_path(self):
        url = self.root_url + 'xxx/sponsor_children?userid=7663'
        response = self.url_open(url)

        self.assertEqual(response.code, 404)
        self.assertEqual(response.msg, "NOT FOUND")
