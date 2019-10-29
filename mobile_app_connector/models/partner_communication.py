# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    firebase_registration_exists = fields.Boolean(
        compute='_compute_firebase_registration_exists')

    mobile_notification_send = fields.Boolean("Send mobile notification", default=False)
    mobile_notification_auto_send = fields.Boolean("Auto send")
    mobile_notification_title = fields.Char("Title")
    mobile_notification_body = fields.Char("Body")

    mobile_notification_destination = fields.Selection([
        ('MyHub', 'My Hub'),
        ('Letter', 'Letter'),
        ('Donation', 'Donation'),
        ('Prayer', 'Prayer'),
    ], "Destination", default="MyHub")

    mobile_notification_topic = fields.Selection([
        ('general_notification', 'General channel'),
        ('child_notification', 'Child channel'),
        ('spam', "None (bypass user's preferences)")
    ], "Topic", default='general_notification')

    mobile_notification = fields.Many2one("firebase.notification")

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []

        default_vals.extend([
            "mobile_notification_send",
            "mobile_notification_auto_send",
            "mobile_notification_title",
            "mobile_notification_body",
            "mobile_notification_destination",
            "mobile_notification_topic",
        ])

        return super(CommunicationJob, self)._get_default_vals(vals, default_vals)

    @api.model
    def send(self):
        """ Create a mobile notification when requested """

        if self.mobile_notification_send:
            mobile_notif = self.env["firebase.notification"].create({
                'title': self.mobile_notification_title,
                'body': self.mobile_notification_body,
                'destination': self.mobile_notification_destination,
                'topic': self.mobile_notification_topic,
            })
            mobile_notif.partner_ids = self.partner_id
            self.mobile_notification = mobile_notif

            if self.mobile_notification_auto_send:
                self.mobile_notification.send()

        return super(CommunicationJob, self).send()

    @api.multi
    def unlink(self):
        self.mobile_notification.unlink()
        return super(CommunicationJob, self).unlink()

    @api.multi
    @api.depends("partner_id")
    def _compute_firebase_registration_exists(self):
        """
            Check whether the partner has at least one registration_id
            (i.e. we can send him a notification, he downloaded and logged in the app)
        """
        for job in self:
            job.firebase_registration_exists = \
                job.partner_id and len(job.partner_id.firebase_registration_ids) > 0

            if not job.firebase_registration_exists:
                job.mobile_notification_send = False
