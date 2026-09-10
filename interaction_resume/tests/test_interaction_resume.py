##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import timedelta
from uuid import uuid4

from odoo import fields
from odoo.tests import HttpCase, tagged

from odoo.addons.base.models.ir_actions_report import IrActionsReport

_pre_render_qweb_pdf = IrActionsReport._pre_render_qweb_pdf


def _force_pdf_rendering(self, report_ref, res_ids=None, data=None):
    return _pre_render_qweb_pdf(
        self.with_context(force_report_rendering=True), report_ref, res_ids, data
    )

ATTACHMENT_NAME = "letter-of-the-sponsor.txt"

LETTER = {
    "subject": "Handwritten letter received at the office",
    "body": "The sponsor wrote to us to ask for news of the sponsored child.",
    "communication_type": "Paper",
    "direction": "in",
    "other_type": False,
    "attachment": ATTACHMENT_NAME,
}
ANSWER = {
    "subject": "Answer written about the sponsored child",
    "body": "We answered the sponsor and told how the sponsored child is doing.",
    "communication_type": "Email",
    "direction": "out",
    "other_type": False,
}
VISIT = {
    "subject": "The sponsor came to visit us",
    "body": "The sponsor came to the office and we handed over the child folder.",
    "communication_type": "Other",
    "direction": "in",
    "other_type": "Visit at the office",
}

INCOMING_CALL = {
    "subject": "The sponsor called about the payment date",
    "body": "The sponsor asked to move the payment to the end of the month.",
    "direction": "in",
}
OUTGOING_CALL = {
    "subject": "We called the sponsor back about the payment date",
    "body": "We confirmed the payment is now taken on the 25th of each month.",
    "direction": "out",
}

EMAIL_COMMUNICATION = {
    "subject": "Confirmation of the new payment date",
    "body": "Dear sponsor, your payment is now taken on the 25th of each month.",
    "send_mode": "digital",
    "communication_type": "Email",
}
PRINTED_COMMUNICATION = {
    "subject": "Yearly news of the sponsored child",
    "body": "Dear sponsor, here are the yearly news of the child you support.",
    "send_mode": "physical",
    "communication_type": "Paper",
}


@tagged("post_install", "-at_install")
class TestInteractionResume(HttpCase):
    """End to end tests of the interaction resume of a contact."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.tour_enabled = False
        cls.admin.lang = "en_US"
        cls.admin.tz = "Europe/Zurich"

        # Print to a PDF rather than to a printer.
        cls.admin.printing_action = "client"
        cls.admin.printing_printer_id = False
        cls.env["printing.printer"].search([("default", "=", True)]).default = False
        cls.report = cls.env.ref("partner_communication.report_a4_communication")
        cls.report.printing_printer_id = False
        cls.report.property_printing_action_id = False
        cls.classPatch(IrActionsReport, "_pre_render_qweb_pdf", _force_pdf_rendering)

        cls.token = uuid4().hex[:12]
        cls.partner = cls.env["res.partner"].create(
            {
                "firstname": "Interaction",
                "lastname": f"Resume {cls.token}",
                "email": f"interaction.resume+{cls.token}@example.org",
                "street": "Rue Galilée 3",
                "zip": "1400",
                "city": "Yverdon-les-Bains",
                "country_id": cls.env.ref("base.ch").id,
                "lang": "en_US",
                "global_communication_delivery_preference": "digital",
            }
        )
        cls.contact_url = f"/odoo/contacts/{cls.partner.id}"

    def _only(self, records, field, value):
        """The single record of the set carrying that value."""
        match = records.filtered(lambda record: record[field] == value)
        self.assertEqual(
            len(match), 1, f"'{value}' should match exactly one {records._name}"
        )
        return match

    def _resume_of(self, subject):
        """The single resume entry of the contact carrying that subject."""
        return self._only(self.partner.interaction_resume_ids, "subject", subject)

    def _assert_logged_in_the_past(self, record):
        """The tours change the date of what they log, so it cannot be now."""
        self.assertLess(
            record.date,
            fields.Datetime.now() - timedelta(hours=12),
            "The date typed in the user interface was not kept",
        )

    def _assert_no_note_about(self, *subjects):
        bodies = " ".join(self.partner.message_ids.mapped("body"))
        for subject in subjects:
            self.assertNotIn(
                subject,
                bodies,
                "The interaction should not be logged as a note on the contact",
            )

    def test_log_interaction(self):
        """Interactions logged by hand reach the resume and stay readable."""
        self.start_tour(
            self.contact_url,
            "interaction_resume_log_interaction",
            login="admin",
            timeout=240,
        )

        interactions = self.env["partner.log.other.interaction"].search(
            [("partner_id", "=", self.partner.id)]
        )
        self.assertEqual(
            len(interactions), 3, "The tour should have logged three interactions"
        )

        for expected in (LETTER, ANSWER, VISIT):
            interaction = self._only(interactions, "subject", expected["subject"])
            self.assertEqual(
                interaction.communication_type, expected["communication_type"]
            )
            self.assertEqual(interaction.direction, expected["direction"])
            self.assertEqual(interaction.other_type, expected["other_type"] or False)
            self.assertIn(expected["body"], interaction.body)
            self._assert_logged_in_the_past(interaction)

            # The file the tour attached is kept on the interaction itself.
            attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", interaction._name),
                    ("res_id", "=", interaction.id),
                ]
            )
            self.assertEqual(
                attachments.mapped("name"),
                [expected["attachment"]] if expected.get("attachment") else [],
            )

            # The same interaction, as the resume of the contact shows it.
            entry = self._resume_of(expected["subject"])
            self.assertEqual(entry.res_model, "partner.log.other.interaction")
            self.assertEqual(entry.res_id, interaction.id)
            self.assertEqual(entry.direction, expected["direction"])
            self.assertEqual(entry.communication_type, expected["communication_type"])
            self.assertEqual(entry.other_type, expected["other_type"] or False)
            self.assertIn(expected["body"], entry.body)
            self.assertEqual(entry.date, interaction.date)
            self.assertEqual(entry.user_id, self.admin)
            self.assertEqual(
                entry.has_attachment,
                bool(expected.get("attachment")),
                "The resume does not say whether the interaction carries a file",
            )

        # Uploading through the wizard must not leave a copy of the file
        # behind on the wizard itself.
        self.assertFalse(
            self.env["ir.attachment"].search_count(
                [
                    ("res_model", "=", "partner.log.other.interaction.wizard"),
                    ("name", "=", ATTACHMENT_NAME),
                ]
            ),
            "The attachment was left behind on the wizard",
        )

        self._assert_no_note_about(
            LETTER["subject"], ANSWER["subject"], VISIT["subject"]
        )

    def test_log_call(self):
        """Calls logged by hand reach the resume, both ways."""
        if not self.env["ir.module.module"].search(
            [("name", "=", "crm_compassion"), ("state", "=", "installed")]
        ):
            self.skipTest("the 'Log your call' action comes with crm_compassion")

        self.start_tour(
            self.contact_url,
            "interaction_resume_log_call",
            login="admin",
            timeout=240,
        )

        calls = self.env["crm.phonecall"].search([("partner_id", "=", self.partner.id)])
        self.assertEqual(len(calls), 2, "The tour should have logged two calls")

        for expected in (INCOMING_CALL, OUTGOING_CALL):
            call = self._only(calls, "name", expected["subject"])
            self.assertEqual(
                call.state, "done", "A logged call is a call that was held"
            )
            self.assertEqual(call.direction, expected["direction"])
            self.assertIn(expected["body"], call.description)
            self._assert_logged_in_the_past(call)

            entry = self._resume_of(expected["subject"])
            self.assertEqual(entry.res_model, "crm.phonecall")
            self.assertEqual(entry.res_id, call.id)
            self.assertEqual(entry.direction, expected["direction"])
            self.assertEqual(entry.communication_type, "Phone")
            self.assertIn(expected["body"], entry.body)
            self.assertEqual(entry.date, call.date)

        self._assert_no_note_about(INCOMING_CALL["subject"], OUTGOING_CALL["subject"])

    def test_communication(self):
        """Communications that are sent reach the resume without a refresh."""
        self.start_tour(
            self.contact_url,
            "interaction_resume_communication",
            login="admin",
            timeout=300,
        )

        jobs = self.env["partner.communication.job"].search(
            [("partner_id", "=", self.partner.id)]
        )
        self.assertEqual(
            len(jobs), 2, "The tour should have created two communications"
        )

        for expected in (EMAIL_COMMUNICATION, PRINTED_COMMUNICATION):
            job = self._only(jobs, "subject", expected["subject"])
            self.assertEqual(job.send_mode, expected["send_mode"])
            self.assertEqual(job.state, "done", "The communication was not sent")
            self.assertTrue(job.sent_date)
            self.assertIn(expected["body"], job.body_html)

            entry = self._resume_of(expected["subject"])
            self.assertEqual(entry.res_model, "partner.communication.job")
            self.assertEqual(entry.res_id, job.id)
            self.assertEqual(entry.direction, "out")
            self.assertEqual(entry.communication_type, expected["communication_type"])
            self.assertIn(expected["body"], entry.body)
            self.assertEqual(entry.date, job.sent_date)

        # The one sent by e-mail produced a mail addressed to the contact.
        email_job = self._only(jobs, "subject", EMAIL_COMMUNICATION["subject"])
        self.assertTrue(email_job.email_id, "Sending the communication made no e-mail")
        self.assertEqual(email_job.email_id.state, "sent")
        self.assertEqual(email_job.email_id.recipient_ids, self.partner)
        self.assertEqual(
            self._resume_of(EMAIL_COMMUNICATION["subject"]).email, self.partner.email
        )

        # The printed one was rendered to a PDF rather than sent to a printer.
        letter_job = self._only(jobs, "subject", PRINTED_COMMUNICATION["subject"])
        self.assertTrue(
            letter_job.printed_pdf_data, "The letter was not rendered to a PDF"
        )
        self.assertTrue(
            base64.b64decode(letter_job.printed_pdf_data).startswith(b"%PDF"),
            "What the letter produced is not a PDF",
        )
        self.assertGreaterEqual(letter_job.pdf_page_count, 1)
