##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models, fields, SUPERUSER_ID, _
from odoo.tools import config
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import messaging
    from firebase_admin import exceptions
except ImportError as e:
    _logger.warning("Please install the PIP package firebase_admin")

try:
    firebase_credentials = credentials.Certificate(
        config.get("google_application_credentials")
    )
    firebase_app = firebase_admin.initialize_app(credential=firebase_credentials)
except (KeyError, ValueError) as e:
    firebase_app = None
    _logger.warning(
        "google_application_credentials is not correctly configured " "in odoo.conf"
    )


class FirebaseNotification(models.Model):
    """
    Represent a mobile notification which can be sent to a set of partners.
    """

    _name = "firebase.notification"
    _rec_name = "title"
    _description = "Notification to send to Firebase Cloud Messaging"
    _order = "send_date desc, id desc"

    color = fields.Integer(
        string='Color Index', compute="_compute_color", inverse="_inverse_color")
    stage_id = fields.Many2one(
        'firebase.notification.stage', 'Stage', ondelete='restrict', required=True,
        default=lambda self: self.env['firebase.notification.stage'].search(
            [], limit=1), group_expand='_group_expand_stage_ids', index=True,
        copy=False)
    partner_ids = fields.Many2many("res.partner", string="Partners", readonly=False)
    title = fields.Char(required=True)
    body = fields.Char(required=True)
    send_date = fields.Datetime(copy=False)
    sent = fields.Boolean(readonly=True, copy=False)
    send_to_logged_out_devices = fields.Boolean(
        default=False, string="Send to devices without logged users."
    )
    read_ids = fields.One2many(
        "firebase.notification.partner.read",
        "notification_id",
        string="Partner read status of the notification",
        readonly=True,
    )
    language = fields.Selection("_get_lang")
    res_model = fields.Char()
    res_id = fields.Integer()
    test_mode = fields.Boolean()
    delivered = fields.Integer(compute="_compute_statistics")
    expected = fields.Integer(compute="_compute_statistics")
    failed = fields.Integer(compute="_compute_statistics", store=True)
    opened = fields.Integer(compute="_compute_statistics", store=True)
    received_ratio = fields.Integer(compute="_compute_statistics")
    failed_ratio = fields.Integer(compute="_compute_statistics")
    opened_ratio = fields.Integer(compute="_compute_statistics")

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        for notification in self:
            stage_id = self.env.ref('firebase_connector.notification_stage_2').id
            if notification.stage_id.id == stage_id:
                if not notification.send_date:
                    dt = fields.Datetime.now()
                    notification.with_context(noonchange=True).send_date = dt

    @api.model
    def create(self, vals):
        if vals.get("res_id") and vals.get("res_model"):
            previous_notification = self.env["firebase.notification"].search([
                ("res_model", "=", vals["res_model"]),
                ("res_id", "=", vals["res_id"])
            ])
            if previous_notification:
                return previous_notification
        return super(FirebaseNotification, self).create(vals)

    @api.depends("test_mode", "stage_id")
    def _compute_color(self):
        for notification in self:
            if notification.test_mode:
                notification.color = 4

    def _inverse_color(self):
        # Allow setting manually a color
        return True

    @api.constrains("send_date")
    def _check_date(self):
        for notif in self:
            if notif.send_date is False:
                continue

            dt = fields.Datetime.now()
            if notif.send_date < dt:
                raise UserError(_("Send date should be in the future"))

    @api.multi
    def send(self, **kwargs):
        """
        This method take a notification object in Odoo and send it to the
        partners devices via Firebase Cloud Messaging. If the notification was
        successfully given to Firebase, we create a
        firebase.notification.partner.read for each partner to track the read
        status of the notification.
        :param data:
        :return:
        """
        if kwargs is None:
            kwargs = {}
        self.write({
            "stage_id": self.env.ref('firebase_connector.notification_stage_3').id})
        self.env.cr.commit()
        for notif in self:
            registration_ids = self.env["firebase.registration"].search(
                [("partner_id", "in", notif.partner_ids.ids)]
            )
            if notif.send_to_logged_out_devices:
                registration_ids += self.env["firebase.registration"].search(
                    [("partner_id", "=", False)]
                )

            # filter registration based on language
            if notif.language:
                registration_ids = registration_ids.filtered(
                    lambda reg: not reg.language or reg.language == notif.language)

            kwargs.update({
                "notification_id": str(notif.id),
                "title": notif.title, "body": notif.body
            })

            split = 500
            nb_batches = len(registration_ids) // split
            remaining = (len(registration_ids) % split) and 1
            status_ok = False
            try:
                for j in range(0, nb_batches + remaining):
                    i = j * split
                    status_ok = status_ok or self.send_multicast_and_handle_errors(
                        registration_ids[i: i + split], notif, kwargs)
                    if status_ok:
                        self.env["firebase.notification.partner.read"].create([
                            {"partner_id": partner.id, "notification_id": notif.id}
                            for partner in registration_ids[i: i + split].exists()
                                .mapped("partner_id")
                        ])
                        self.env.cr.commit()
                notif.sent = status_ok

                if status_ok:
                    notif.send_date = fields.Datetime.now()
                    notif.stage_id = self.env.ref(
                        'firebase_connector.notification_stage_4').id
                    self.env.cr.commit()
            except:
                self.env.clear()
                _logger.error("Error while sending notifications", exc_info=True)

    @api.multi
    def send_multicast_and_handle_errors(self, registration_ids, notif, data=None):
        if not firebase_app:
            _logger.error(
                "google_application_credentials is not correctly "
                "configured in odoo.conf or invalid. Skipping "
                "sending notifications"
            )
            return False

        notification = messaging.Notification(title=notif.title, body=notif.body)
        registration_tokens = []
        for token in registration_ids:
            registration_tokens.append(token.registration_id)
        if registration_tokens:
            multicast_message = messaging.MulticastMessage(
                notification=notification,
                data=data,
                tokens=registration_tokens
            )

            try:
                response = messaging.send_multicast(
                    multicast_message, dry_run=self.test_mode)
                _logger.info(
                    '{0} messages were sent successfully'.format(response.success_count)
                )
                responses = response.responses
                failed_tokens = []
                for idx, resp in enumerate(responses):
                    registration_id = self.env["firebase.registration"] \
                        .search([("registration_id", "=", registration_tokens[idx])])
                    if not resp.success:
                        failed_tokens.append(registration_tokens[idx])
                        self.env["firebase.notification.statistics"].create({
                            "code": resp.exception.code,
                            "notification_id": notif.id,
                            "delivered": False, "failed": True,
                            "create_date": fields.Datetime.now(),
                            "registration_id": registration_id.id
                        })
                        if resp.exception.code == exceptions.NOT_FOUND:
                            _logger.debug(
                                "A device is not reachable from Firebase, unlinking."
                                "Firebase ID: %s" % registration_tokens[idx]
                            )
                            if registration_id:
                                registration_id.unlink()
                    else:
                        self.env["firebase.notification.statistics"].create({
                            "code": "success",
                            "notification_id": notif.id,
                            "delivered": True,
                            "failed": False,
                            "create_date": fields.Datetime.now(),
                            "registration_id": registration_id.id}
                        )
                _logger.warning(
                    'List of tokens that caused failures: {0}'.format(failed_tokens)
                )

                if response.success_count > 0:
                    return True
            except (
                    messaging.QuotaExceededError,
                    messaging.SenderIdMismatchError,
                    messaging.ThirdPartyAuthError,
                    messaging.UnregisteredError,
                    exceptions.FirebaseError,
            ) as ex:
                _logger.error(ex)
                # Save error in ir.logging to allow tracking of errors
                self.env["ir.logging"].create(
                    {
                        "name": "Firebase " + ex.__class__.__name__,
                        "type": "server",
                        "message": ex,
                        "path": "/firebase_connector/models/firebase_regitration.py",
                        "line": "100",
                        "func": "send_message",
                    }
                )

    @api.multi
    def duplicate_to_unread(self):
        self.ensure_one()

        unread_partner_ids = self.partner_ids - self.read_ids.filtered("opened").mapped(
            "partner_id"
        )

        duplicate = self.create(
            {
                "title": self.title,
                "body": self.body,
                "send_to_logged_out_devices": self.send_to_logged_out_devices,
                "partner_ids": [(6, False, unread_partner_ids.ids)],
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Notification",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": duplicate.id,
            "target": "current",
        }

    def notification_cron(self):
        dt = fields.Datetime.now()
        stage_id = self.env.ref('firebase_connector.notification_stage_2').id
        self.search([
            ("sent", "=", False),
            ("send_date", "<", dt),
            ("stage_id", "=", stage_id)
        ]).send()
        return True

    @api.multi
    def schedule(self):
        stage_id = self.env.ref('firebase_connector.notification_stage_2').id
        if self.send_date:
            self.write(dict(stage_id=stage_id))
        else:
            dt = fields.Datetime.now()
            self.write(dict(stage_id=stage_id, send_date=dt))

    def _compute_statistics(self):
        self.env.cr.execute("""
                    SELECT
                        n.id as notification_id,
                        COUNT(s.id) AS expected,
                        COUNT(CASE WHEN s.delivered THEN 1 ELSE null END) AS delivered,
                        COUNT(CASE WHEN s.failed THEN 1 ELSE null END) AS failed,
                        COUNT(CASE WHEN r.opened THEN 1 ELSE null END) AS opened
                    FROM
                        firebase_notification_statistics s
                    RIGHT JOIN
                        firebase_notification n
                        ON (n.id = s.notification_id)
                    RIGHT JOIN firebase_notification_partner_read r
                        ON (n.id = r.notification_id)
                    WHERE
                        n.id IN %s
                    GROUP BY
                        n.id
                """, (tuple(self.ids),))
        for row in self.env.cr.dictfetchall():
            total = row['expected'] or 1
            row['opened_ratio'] = 100.0 * row['opened'] / total
            row['received_ratio'] = 100.0 * row['delivered'] / total
            row['failed_ratio'] = 100.0 * row['failed'] / total
            self.browse(row.pop('notification_id')).update(row)

    @api.model
    def _group_expand_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)


class FirebaseNotificationPartnerRead(models.Model):
    """
    Link a notification to a partner read status
    """

    _name = "firebase.notification.partner.read"
    _description = "Link between partner and notifications read status"

    partner_id = fields.Many2one(
        "res.partner", "Partner", ondelete="cascade", index=True, readonly=False
    )
    notification_id = fields.Many2one(
        "firebase.notification",
        "Notification",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=False,
    )
    opened = fields.Boolean(default=False)
    read_date = fields.Datetime()
