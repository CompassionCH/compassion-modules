##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class FirebaseNotification(models.Model):
    _inherit = "firebase.notification"

    destination = fields.Selection(
        [
            ("MyHub", "My Hub"),
            ("Letter", "Letter"),
            ("Donation", "Donation"),
            ("Prayer", "Prayer"),
        ],
        default="MyHub",
    )

    topic = fields.Selection(
        [
            ("general_notification", "General channel"),
            ("child_notification", "Child channel"),
            ("spam", "None (bypass user's preferences)"),
        ],
        default="general_notification",
        required=True,
    )

    fundType = fields.Many2one("product.product", "Fund product", readonly=False)
    child_id = fields.Many2one("compassion.child", "Child", readonly=False)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.multi
    def send(self, **kwargs):
        """
        Filters notifications w.r.t. user's preference

        :param data:
        :return:
        """
        data = kwargs.get("data", {})

        for notif in self:
            data.update({
                "topic": notif.topic,
                "destination": notif.destination or "",
                "fund_type_id": str(notif.fundType.id),
            })
            super(FirebaseNotification, notif).send(**data)

    def duplicate_to_unread(self):
        res = super().duplicate_to_unread()
        new = self.browse(res["res_id"])
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
        firebase_id = params.get("firebase_id")
        reg = self.env["firebase.registration"].search(
            [("registration_id", "=", firebase_id)]
        )

        dt = fields.Datetime.now()
        # Logged out notifications
        notifications = self.search(
            [
                ("send_to_logged_out_devices", "=", True),
                ("send_date", "<", dt),
                ("sent", "=", True),
            ]
        )
        if reg.partner_id:
            # Logged in notifications
            notifications += self.search(
                [
                    ("partner_ids", "=", reg.partner_id.id),
                    ("send_date", "<", dt),
                    ("sent", "=", True),
                ]
            )

        messages = []
        for notif in notifications:
            is_read = (
                "1"
                if notif.read_ids.filtered(
                    lambda r: r.partner_id == reg.partner_id
                ).opened
                else "0"
            )

            messages.append(
                {
                    "CHILD_IMAGE": notif.child_id.pictures_ids[:1].image_url_compassion,
                    "CHILD_NAME": "",
                    "CREATED_BY": "",
                    "CREATED_ON": notif.send_date,
                    "DESTINATION": notif.destination,
                    "DISPLAY_ORDER": "",
                    "HERO": "",
                    "ID": str(notif.id),
                    "IS_DELETED": "",
                    "MESSAGE_BODY": notif.body,
                    "MESSAGE_TITLE": notif.title,
                    "MESSAGE_TYPE": "",
                    "NEEDKEY": notif.child_id.local_id,
                    "OA_BRAND_ID": "",
                    "OA_ID": "",
                    "SEND_NOTIFICATION": "",
                    "STATUS": "",
                    "SUPPORTER_ID": "",
                    "SUPPORTER_NAME": "",
                    "UPDATED_BY": "",
                    "UPDATED_ON": notif.send_date,
                    "USER_ID": "",
                    "IS_READ": is_read,
                    "POST_TITLE": str(notif.fundType.id),
                }
            )

        return messages


class FirebaseNotificationPartnerRead(models.Model):
    """
    Link a notification to a partner read status
    """

    _inherit = "firebase.notification.partner.read"

    def mobile_read_notification(self, *json, **params):
        notif_id = params.get("notification_id")
        notif = self.env["firebase.notification.partner.read"].search(
            [
                ("notification_id", "=", int(notif_id)),
                ("partner_id", "=", self.env.user.partner_id.id),
            ]
        )
        notif.opened = True
        notif.read_date = fields.Datetime.now()
        return 1
