# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class FirebaseNotification(models.Model):
    """
    Represent a mobile notification which can be sent to a set of partners.
    """
    _name = 'firebase.notification'
    _description = 'Notification to send to Firebase Cloud Messaging'
    _order = 'send_date desc'

    partner_ids = fields.Many2many('res.partner', string="Partners")
    title = fields.Char(required=True)
    body = fields.Char(required=True)
    send_date = fields.Datetime()
    sent = fields.Boolean(readonly=True)
    send_to_logged_out_devices = fields.Boolean(
        default=False, string="Send to devices without logged users.")
    read_ids = fields.One2many(
        'firebase.notification.partner.read', 'notification_id',
        string='Partner read status of the notification', readonly=True)

    @api.constrains('send_date')
    def _check_date(self):
        for notif in self:
            if notif.send_date is False:
                continue

            dt = fields.Datetime.now()
            if notif.send_date < dt:
                raise UserError(_("Send date should be in the future"))

    @api.multi
    def send(self, data=None):
        """
        This method take a notification object in Odoo and send it to the
        partners devices via Firebase Cloud Messaging. If the notification was
        successfully given to Firebase, we create a
        firebase.notification.partner.read for each partner to track the read
        status of the notification.
        :param data:
        :return:
        """
        if data is None:
            data = {}

        for notif in self:
            registration_ids = self.env['firebase.registration'].search([
                ('partner_id', 'in', notif.partner_ids.ids)
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
                    self.env['firebase.notification.partner.read'].create({
                        'partner_id': partner.id,
                        'notification_id': notif.id,
                    })

    @api.multi
    def duplicate_to_unread(self):
        self.ensure_one()

        unread_partner_ids = self.partner_ids - self.read_ids.filtered('opened')\
            .mapped('partner_id')

        duplicate = self.create({
            'title': self.title,
            'body': self.body,
            'send_to_logged_out_devices': self.send_to_logged_out_devices,
            'partner_ids': [(6, False, unread_partner_ids.ids)]
        })

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
        dt = fields.Datetime.now()
        self.search([
            ('sent', '=', False),
            ('send_date', '<', dt)
        ]).send()

        return True


class FirebaseNotificationPartnerRead(models.Model):
    """
    Link a notification to a partner read status
    """
    _name = "firebase.notification.partner.read"
    _description = "Link between partner and notifications read status"

    partner_id = fields.Many2one('res.partner',
                                 'Partner',
                                 ondelete='cascade',
                                 index=True)
    notification_id = fields.Many2one('firebase.notification',
                                      'Notification',
                                      required=True,
                                      ondelete="cascade",
                                      index=True)
    opened = fields.Boolean(default=False)
    read_date = fields.Datetime()
