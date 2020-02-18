# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    firebase_registration_exists = fields.Boolean(
        compute='_compute_firebase_registration_exists')

    mobile_notification_send = fields.Boolean("Send mobile notification", default=False)
    mobile_notification_auto_send = fields.Boolean("Auto send")
    mobile_notification_title = fields.Text("Title")
    mobile_notification_body = fields.Text("Body")

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

    mobile_notification_id = fields.Many2one(
        "firebase.notification", "Notification", copy=False)

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

    @api.multi
    def send(self):
        """ Create a mobile notification when requested """
        jobs = self.filtered(lambda j: j.state == 'pending')\
            .filtered('mobile_notification_send')\
            .filtered('firebase_registration_exists')
        res = super(CommunicationJob, self).send()

        for job in jobs:
            template = job.email_template_id
            # For notifications, we take only the first related object (no multi-mode)
            # to render the notification text.
            object = self.get_objects()[:1]
            mobile_notif = job.env["firebase.notification"].create({
                'title': template.render_template(
                    job.mobile_notification_title, object._name, object.id),
                'body': template.render_template(
                    job.mobile_notification_body, object._name, object.id),
                'destination': job.mobile_notification_destination,
                'topic': job.mobile_notification_topic,
                'partner_ids': [(4, job.partner_id.id)]
            })
            job.mobile_notification_id = mobile_notif

            if job.mobile_notification_auto_send:
                job.mobile_notification_id.send()

        return res

    @api.multi
    def unlink(self):
        self.mapped('mobile_notification_id').filtered(lambda n: not n.sent).unlink()
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
