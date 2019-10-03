# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models
from odoo.fields import Datetime


class FirebaseNotification(models.Model):
    _inherit = "firebase.notification"

    destination = fields.Selection([
        ('MyHub', 'MyHub'),
        ('Letter', 'Letter'),
        ('Donation', 'Donation'),
        ('Prayer', 'Prayer'),
    ], default="MyHub")

    fundType = fields.Many2one('product.product')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def duplicate_to_unread(self):
        res = super(FirebaseNotification, self).duplicate_to_unread()
        new = self.browse(res['res_id'])
        new.destination = self.destination
        new.fundType = self.fundType
        return res

    @api.model
    def mobile_get_notification(self, **params):
        """
        This is called when the app retrieves the notification.
        :param params: {
            firebase_id: the device id requesting its notifications,
            supid: id of the partner logged in the app
        }
        :return: a list of notifications as expected by the app
        """
        firebase_id = params.get('firebase_id')
        reg = self.env['firebase.registration']\
            .search([('registration_id', '=', firebase_id)])
        if reg.partner_id:
            notifications = self.search([
                ('partner_ids', '=', reg.partner_id.id,),
                ('send_date', '<', Datetime.now()),
            ])
        else:
            # Logged out users
            notifications = self.search([
                ('send_to_logged_out_devices', '=', True)])
        messages = []
        for notif in notifications:
            messages.append({
                "CHILD_IMAGE": "",
                "CHILD_NAME": "",
                "CREATED_BY": "",
                "CREATED_ON": "",
                "DESTINATION": notif.destination,
                "DISPLAY_ORDER": "",
                "HERO": "",
                "ID": notif.id,
                "IS_DELETED": "",
                "MESSAGE_BODY": notif.body,
                "MESSAGE_TITLE": notif.title,
                "MESSAGE_TYPE": "",
                "NEEDKEY": "",
                "OA_BRAND_ID": "",
                "OA_ID": "",
                "SEND_NOTIFICATION": "",
                "STATUS": "",
                "SUPPORTER_ID": "",
                "SUPPORTER_NAME": "",
                "UPDATED_BY": "",
                "UPDATED_ON": "",
                "USER_ID": "",
                "IS_READ": "0" if reg.partner_id in notif.read_ids.mapped('partner_id') else "1",
                "POST_TITLE": notif.fundType.id,
            })

        return messages


class FirebaseNotificationPartnerRead(models.Model):
    """
    Link a notification to a partner read status
    """
    _inherit = "firebase.notification.partner.read"

    def mobile_read_notification(self, *json, **params):
        notif_id = params.get('notification_id')
        # TODO fix permissions
        # notif = self.sudo().browse(int(notif_id))
        # notif.opened = True
        # notif.read_date = fields.Datetime.today()
        return 1
