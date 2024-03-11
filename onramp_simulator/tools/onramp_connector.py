##############################################################################
#
#    Copyright (C) 2015-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json

from odoo.addons.message_center_compassion.tools.onramp_connector import OnrampConnector


class TestOnrampConnector:
    def __init__(self, env):
        self.connector = OnrampConnector(env)

    def test_message(self, test_message):
        """Sends a message to any onramp.
        :param test_message (onramp.simulator record): the message to send
        """
        country_code = self.connector._res_config.env["res.company"]._get_main_company(
            
        ).country_id.code
        headers = {
            "Content-type": "application/json",
            "x-cim-MessageType": test_message.message_type_url,
            "x-cim-FromAddress": "OnrampSimulator",
            "x-cim-ToAddress": country_code,
        }
        url = test_message.server_url
        body = test_message.body_json

        r = self.connector.send_message(
            url, "POST", headers=headers, body=json.loads(body), full_url=True
        )
        test_message.write(
            {"result": str(r.get("content")), "result_code": r.get("code")}
        )
