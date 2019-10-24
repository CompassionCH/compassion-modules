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
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import messaging
except ImportError as e:
    _logger.error("Please install the PIP package firebase_admin")


class FirebaseNotification(models.Model):
    """
    The represent a device that we can send push notification to. It is
    characterized by the Firebase token and an optional partner.
    It provides function to send messages to the device.
    """

    _name = 'firebase.notification'
    _description = 'Notification to send to Firebase Cloud Messaging'

    partner_ids = fields.Many2many('res.partner')
    title = fields.Char(required=True)
    body = fields.Char(required=True)
    send_date = fields.Datetime()
    sent = fields.Boolean(default=False, readonly=True)
    send_to_logged_out_devices = fields.Boolean(
        default=False, string="Send to devices without logged users.")
    read_ids = fields.One2many(
        'firebase.notification.partner.read', 'notification_id',
        string='Partner read status of the notification', readonly=True)

    @api.multi
    def write(self, vals):
        res = super(FirebaseNotification, self).write(vals)
        if 'send_date' in vals:
            dt = datetime.strftime(datetime.today(), "%Y-%m-%d %H:%M:%S")
            if vals['send_date'] < dt:
                raise UserError(_("Send date should be in the future"))
        return res

    @api.multi
    def send(self, data={}):
        """
        This method take a notification object in Odoo and send it to the
        partners devices via Firebase Cloud Messaging. If the notification was
        successfully given to Firebase, we create a
        firebase.notification.partner.read for each partner to track the read
        status of the notification.
        :param data:
        :return:
        """
        for notif in self:
            registration_ids = self.env['firebase.registration'].search([
                ('partner_id', 'in', notif.partner_ids.mapped('id'))
            ])
            if notif.send_to_logged_out_devices:
                registration_ids += self.env['firebase.registration'].search(
                    [('partner_id', '=', False)]
                )

            data.update({
                "notification_id": str(notif.id),
            })

            notif.sent = registration_ids.send_message(notif.title, notif.body, data)
            if notif.sent:
                notif.send_date = fields.Datetime.now()
                for partner in notif.partner_ids:
                    notif.read_ids += \
                        self.env['firebase.notification.partner.read'].create({
                            'partner_id': partner.id,
                            'notification_id': notif.id,
                        })
            else:
                raise UserError(_("We were not able to send the notification."))

    @api.multi
    def duplicate_to_unread(self):
        for notif in self:
            duplicate = self.create({
                'title': notif.title,
                'body': notif.body,
                'send_to_logged_out_devices': notif.send_to_logged_out_devices,
            })
            # Doesn't work if put directly in the record creation
            duplicate.partner_ids = [
                p.id for p in notif.partner_ids
                if p not in notif.read_ids.mapped('partner_id.id')
            ],
            return {
                'type': 'ir.actions.act_window',
                'name': 'Notification',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'res_id': duplicate.id,
                'target': 'current',
            }

    def notification_cron(self):
        dt = datetime.strftime(datetime.today(), "%Y-%m-%d %H:%M:%S")

        self.search([
            ('sent', '=', False),
            ('send_date', '<', dt)
        ]).send()


class FirebaseNotificationPartnerRead(models.Model):
    """
    Link a notification to a partner read status
    """
    _name = "firebase.notification.partner.read"
    _description = "Link between partner and notifications read status"

    partner_id = fields.Many2one('res.partner')
    notification_id = fields.Many2one('firebase.notification', required=True, ondelete="cascade")
    opened = fields.Boolean(default=False)
    read_date = fields.Datetime()
