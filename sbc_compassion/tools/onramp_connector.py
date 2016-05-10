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
import logging
import base64

from openerp import _
from openerp.exceptions import Warning
from openerp.addons.message_center_compassion.tools.onramp_connector import \
    OnrampConnector

logger = logging.getLogger(__name__)


class SBCConnector(OnrampConnector):
    """ Singleton class to connect to U.S. Onramp in order to send
    messages. """

    def send_letter_image(self, image_data, image_type):
        """ Sends an image of a Letter to Onramp U.S. Image Upload Service.
        See http://developer.compassion.com/docs/read/compassion_connect2/
            service_catalog/Image_Submission

        Returns the uploaded image URL.
        """
        headers = {'Content-type': 'image/{0}'.format(image_type)}
        params = {'doctype': 's2bletter'}
        url = self._connect_url+'images/documents'
        self._log_message(
            'POST', url, headers, '{image binary data not shown}')
        r = self._session.post(
            url, params=params, headers=headers,
            data=base64.b64decode(image_data))
        letter_url = False
        status = r.status_code
        if status == 201:
            letter_url = r.text
        else:
            raise Warning(
                _("Error while uploading letter image to GMC."),
                '[%s] %s' % (r.status_code, r.text))
        return letter_url

    def get_letter_image(self, letter_url, type='jpeg', pages=0, dpi=96):
        """ Calls Letter Image Service from Onramp U.S. and get the data
        http://developer.compassion.com/docs/read/compassion_connect2/
        service_catalog/Image_Retrieval
        """
        params = {
            'format': type,
            'pg': pages,
            'dpi': dpi}
        self._log_message('GET', letter_url)
        r = self._session.get(letter_url, params=params)
        letter_data = None
        if r.status_code == 200:
            letter_data = base64.b64encode(r.content)
        return letter_data
