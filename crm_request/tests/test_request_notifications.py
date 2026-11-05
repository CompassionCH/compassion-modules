##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged

EMAIL = """Return-Path: <form@example.com>
From: Website form <form@example.com>
Reply-To: volunteer-t3647@example.com
To: {to}
Subject: T3647 I want to help
Message-ID: <t3647-{token}@example.com>
Date: Wed, 04 Nov 2026 10:00:00 +0100
Content-Type: text/plain; charset=utf-8

I would like to know more about praying.
"""


@tagged("post_install", "-at_install")
class TestRequestNotifications(TransactionCase):
    """The responsible of a request created by e-mail gets one e-mail
    (T3647)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.responsible = cls.env["res.users"].create(
            {
                "name": "T3647 responsible",
                "login": "t3647-responsible",
                "email": "t3647-responsible@example.com",
                "notification_type": "email",
                "groups_id": [(6, 0, cls.env.ref("base.group_user").ids)],
            }
        )
        cls.alias = cls.env["mail.alias"].create(
            {
                "alias_name": "t3647-participate",
                "alias_model_id": cls.env["ir.model"]._get_id("crm.claim"),
                "alias_defaults": f"{{'user_id': {cls.responsible.id}}}",
                "alias_contact": "everyone",
            }
        )

    def receive(self, token):
        thread_id = self.env["mail.thread"].message_process(
            "crm.claim",
            EMAIL.format(token=token, to=self.alias.alias_full_name or "t3647"),
        )
        return self.env["crm.claim"].browse(thread_id)

    def notifications(self, request):
        return self.env["mail.notification"].search(
            [
                ("mail_message_id.model", "=", "crm.claim"),
                ("mail_message_id.res_id", "=", request.id),
                ("res_partner_id", "=", self.responsible.partner_id.id),
            ]
        )

    def test_one_email_for_the_responsible(self):
        request = self.receive("one")

        self.assertEqual(request.user_id, self.responsible)
        self.assertIn(self.responsible.partner_id, request.message_partner_ids)
        notifications = self.notifications(request)
        self.assertEqual(
            notifications.mail_message_id.mapped("message_type"),
            ["email"],
            "The responsible should only get the incoming e-mail, not the "
            "'You have been assigned' e-mail as well",
        )

    def test_assigning_by_hand_still_notifies(self):
        request = self.receive("by-hand")
        other = self.responsible.copy({"login": "t3647-other"})

        request.user_id = other

        assigned = self.env["mail.message"].search(
            [
                ("model", "=", "crm.claim"),
                ("res_id", "=", request.id),
                ("message_type", "=", "user_notification"),
                ("partner_ids", "in", other.partner_id.ids),
            ]
        )
        self.assertTrue(assigned)
