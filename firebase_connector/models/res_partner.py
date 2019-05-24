# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class GetPartnerMessage(models.Model):
    _inherit = "res.partner"

    firebase_registration_ids = fields.One2many(
        'firebase.registration', 'partner_id', readonly=True
    )

    def send_notification(self, message_title, message_body, all_device=True):
        """
        Send a notification to the device registered by the user.
        :param message_title: Title of the notification
        :param message_body: Content of the notification
        :param all_device: Flag to send the notification to all the devices.
                           If false, send to the first one of the list.
        :return: Nothing
        """
        if all_device:
            for reg in self.firebase_registration_ids:
                reg.send_message(message_title, message_body)
        else:
            self.firebase_registration_ids[0].send_message(message_title,
                                                           message_body)
