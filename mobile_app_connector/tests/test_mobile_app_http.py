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
from odoo.tests.common import HttpCase
import json


class TestMobileAppHttp(HttpCase):

    def setUp(self):
        super(TestMobileAppHttp, self).setUp()
        self.root_url = '/mobile-app-api/'
        self.opener.addheaders.append(('Content-Type', 'application/json'))

    def test_missing_parameters(self):
        url = self.root_url + 'compassion.child/get_letters'
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
