##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class FirebaseRegistration(models.Model):
    """
    The represent a device that we can send push notification to. It is
    characterized by the Firebase token and an optional partner.
    It provides function to send messages to the device.
    """

    _name = "firebase.registration"
    _description = "Device registered with Firebase Cloud Messaging"
    _rec_name = "registration_id"
    _order = "id desc"

    registration_id = fields.Char("Firebase Registration ID", required=True, index=True)
    partner_id = fields.Many2one("res.partner", "Partner", readonly=False)
    partner_name = fields.Char(related="partner_id.name", readonly=True)

    _sql_constraints = [
        (
            "firebase_id_unique",
            "UNIQUE(registration_id)",
            "Firebase registration ID should be unique",
        )
    ]

    def send_message_from_interface(self):
        """
        Allows to send a notification from Odoo web interface.
        Button is in the form view but generally hidden.
        :return: None
        """

        self.send_message(
            self.env.context.get("message_title"), self.env.context.get("message_body")
        )
