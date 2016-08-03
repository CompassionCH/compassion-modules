# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import simplejson
from openerp.addons.message_center_compassion.tools.onramp_connector import \
    OnrampConnector


class TestOnrampConnector(OnrampConnector):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    def test_message(self, test_message):
        """ Sends a message to any onramp.
        :param test_message (onramp.simulator record): the message to send
        """
        headers = {
            'Content-type': 'application/json',
            'x-cim-MessageType': test_message.message_type_url,
            'x-cim-FromAddress': 'CHTest',
            'x-cim-ToAddress': 'CH'
        }
        url = test_message.server_url
        body = test_message.body_json

        self._log_message('POST', url, headers, body)
        r = self._session.post(url, headers=headers,
                               json=simplejson.loads(body))
        status = r.status_code
        self._log_message(status, 'RESULT', message=r.text)
        test_message.write({
            'result': r.text,
            'result_code': r.status_code
        })
