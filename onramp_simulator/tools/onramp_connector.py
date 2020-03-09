##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import requests
import simplejson
from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector

from odoo import _
from odoo.exceptions import UserError
from odoo.tools.config import config


class TestOnrampConnector(OnrampConnector):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    # Private instance of the class
    __instance = None

    def __new__(cls):
        """ Inherit method to ensure a single instance exists. """
        if TestOnrampConnector.__instance is None:
            TestOnrampConnector.__instance = object.__new__(cls)
            connect_url = config.get("connect_url")
            api_key = config.get("connect_api_key")
            if connect_url and api_key:
                TestOnrampConnector.__instance._connect_url = connect_url
                TestOnrampConnector.__instance._api_key = api_key
                session = requests.Session()
                session.params.update({"api_key": api_key})
                TestOnrampConnector.__instance._session = session
            else:
                raise UserError(
                    _(
                        "Please give connect_url and connect_api_key values "
                        "in your Odoo configuration file."
                    )
                )
        return TestOnrampConnector.__instance

    def test_message(self, test_message):
        """ Sends a message to any onramp.
        :param test_message (onramp.simulator record): the message to send
        """
        headers = {
            "Content-type": "application/json",
            "x-cim-MessageType": test_message.message_type_url,
            "x-cim-FromAddress": "CHTest",
            "x-cim-ToAddress": "CH",
        }
        url = test_message.server_url
        body = test_message.body_json

        OnrampConnector.log_message("POST", url, headers, body)
        r = self._session.post(url, headers=headers, json=simplejson.loads(body))
        status = r.status_code
        OnrampConnector.log_message(status, "RESULT", message=r.text)
        test_message.write({"result": r.text, "result_code": r.status_code})
