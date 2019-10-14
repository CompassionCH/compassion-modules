# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields
from odoo.tools import config
import logging

_logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import messaging
except ImportError as e:
    _logger.error("Please install the PIP package firebase_admin")

try:
    firebase_credentials = credentials.Certificate(config.get('google_application_credentials'))
    firebase_app = firebase_admin.initialize_app(credential=firebase_credentials)
except (KeyError, ValueError) as e:
    firebase_app = None
    logging.error(e)
    if not config.get("test_enable"):
        logging.error("google_application_credentials is not correctly configured in odoo.conf")


class FirebaseRegistration(models.Model):
    """
    The represent a device that we can send push notification to. It is
    characterized by the Firebase token and an optional partner.
    It provides function to send messages to the device.
    """

    _name = 'firebase.registration'
    _description = 'Device registered with Firebase Cloud Messaging'
    _rec_name = 'registration_id'

    registration_id = fields.Char(required=True,
                                  string="Firebase Registration ID")
    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_name = fields.Char(related='partner_id.name', readonly=True)

    _sql_constraints = [
        ('firebase_id_unique',
         'UNIQUE(registration_id)',
         'Firebase registration ID should be unique')]

    def send_message_from_interface(self):
        """
        Allows to send a notification from Odoo web interface.
        Button is in the form view but generally hidden.
        :return: None
        """

        self.send_message(self.env.context.get('message_title'),
                          self.env.context.get('message_body'))

    @api.multi
    def send_message(self, message_title, message_body, data={}):
        """
        Send a notification to the device registered with this firebase id.
        If the firebase id is not in use anymore, we remove the registration
        from the database.
        :param message_title: Title of the notification
        :param message_body: Content of the notification
        :param data: Data segment of a Firebase message (see the docs)
        :return: None
        """

        if not firebase_app:
            logging.error("google_application_credentials is not correctly"
                          "configured in odoo.conf or invalid. Skipping "
                          "sending notifications")
            return False

        notif = messaging.Notification(title=message_title, body=message_body)

        for firebase_id in self:
            data.update({
                'title': message_title,
                'body': message_body
            })
            message = messaging.Message(notification=notif,
                                        data=data,
                                        token=firebase_id.registration_id)
            try:
                messaging.send(message=message)
            except (messaging.QuotaExceededError, messaging.SenderIdMismatchError, messaging.ThirdPartyAuthError,
                    messaging.UnregisteredError) as e:
                logging.error(e)
                if e.code == 'NOT_FOUND':
                    logging.debug(
                        "A device is not reachable from Firebase, unlinking."
                        "Firebase ID: %s" % firebase_id)
                    firebase_id.unlink()
                else:
                    raise e
        return True
