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
import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)

try:
    import simplejson
except ImportError:
    _logger.warning("Please install httplib and simplejson")


class TestOnramp(common.HttpCase):
    """ Base class for all Onramp tests. """

    def setUp(self):
        # Add special controller for decoding a fake Oauth token and posting
        # messages with GMC token
        super(TestOnramp, self).setUp()

        # This is because the request sent is treated as regular http
        # instead of json. TODO find a way for sending proper json request.
        self.rest_url = '/onramp-test'
        headers = [
            ('content-type', 'application/json'),
            ('Authorization', 'Bearer fake_token'),
            ("x-cim-MessageType", "http://schemas.ci.org/ci/services/"
                "communications/2015/09/SBCStructured"),
            ("x-cim-FromAddress", "CHTest"),
            ("x-cim-ToAddress", "CH"),
        ]
        self.opener.addheaders.extend(headers)

    def _send_post(self, vals):
        """
        Used to POST Json data to local onramp.
        :param vals: json data
        :return: Return message from local onramp.
        """
        data = simplejson.dumps(vals)
        return self.url_open(self.rest_url, data)
