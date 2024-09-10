##############################################################################
#
#    Copyright (C) 2015-2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Yannick Vaucher, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import common
from odoo.tools import config

HOST = "127.0.0.1"
PORT = config["http_port"]


class TestOnramp(common.HttpCase):
    """Base class for all Onramp tests."""

    def setUp(self):
        # Add special controller for decoding a fake Oauth token and posting
        # messages with GMC token
        super().setUp()

        # This is because the request sent is treated as regular http
        # instead of json. TODO find a way for sending proper json request.
        self.rest_url = "/onramp"
        headers = {
            "content-type": "application/json",
            "Authorization": "Bearer fake_token",
            "x-cim-MessageType": "http://schemas.ci.org/ci/services/"
            "communications/2015/09/SBCStructured",
            "x-cim-FromAddress": "OnrampSimulator",
            "x-cim-ToAddress": "CH",
        }
        self.opener.headers.update(headers)

    def _send_post(self, vals):
        """
        Used to POST Json data to local onramp.
        :param vals: json data
        :return: Return message from local onramp.
        """
        url = f"http://{HOST}:{PORT}{self.rest_url}"
        return self.opener.post(url, json=vals, timeout=10)
