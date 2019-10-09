# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import base64
import requests

from odoo import _
from odoo.exceptions import UserError
from odoo.addons.message_center_compassion.tools.onramp_connector import \
    OnrampConnector

from odoo.tools.config import config


logger = logging.getLogger(__name__)


class SBCConnector(OnrampConnector):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """
    # Private instance of the class
    __instance = None

    def __new__(cls):
        """ Inherit method to ensure a single instance exists. """
        if SBCConnector.__instance is None:
            SBCConnector.__instance = object.__new__(cls)
            connect_url = config.get('connect_url')
            api_key = config.get('connect_api_key')
            if connect_url and api_key:
                SBCConnector.__instance._connect_url = connect_url
                SBCConnector.__instance._api_key = api_key
                session = requests.Session()
                session.params.update({
                    'api_key': api_key,
                    'gpid': 'CH'
                })
                SBCConnector.__instance._session = session
            else:
                raise UserError(
                    _('Please give connect_url and connect_api_key values '
                      'in your Odoo configuration file.'))
        return SBCConnector.__instance

    def send_letter_image(self, image_data, image_type):
        """ Sends an image of a Letter to Onramp U.S. Image Upload Service.
        See http://developer.compassion.com/docs/read/compassion_connect2/
            service_catalog/Image_Submission

        Returns the uploaded image URL.
        """
        headers = {'Content-type': 'image/{0}'.format(image_type)}
        params = {'doctype': 's2bletter'}
        url = self._connect_url+'images/documents'
        OnrampConnector.log_message(
            'POST', url, headers, message='{image binary data not shown}')
        r = self._session.post(
            url, params=params, headers=headers,
            data=base64.b64decode(image_data))
        status = r.status_code
        if status == 201:
            letter_url = r.text
        else:
            raise UserError(
                _('[%s] %s') % (r.status_code, r.text))
        return letter_url

    def get_letter_image(self, letter_url, img_type='jpeg', pages=0, dpi=96):
        """ Calls Letter Image Service from Onramp U.S. and get the data
        http://developer.compassion.com/docs/read/compassion_connect2/
        service_catalog/Image_Retrieval
        """
        params = {
            'format': img_type,
            'pg': pages,
            'dpi': dpi}
        OnrampConnector.log_message('GET', letter_url)
        r = self._session.get(letter_url, params=params)
        letter_data = None
        if r.status_code == 200:
            letter_data = base64.b64encode(r.content)
        return letter_data
