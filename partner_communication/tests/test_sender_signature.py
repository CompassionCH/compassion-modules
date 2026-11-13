import re

from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSenderSignature(TransactionCase):
    """The signature at the end of a communication follows its sender."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        users = cls.env["res.users"].with_context(no_reset_password=True)
        signature_is_stored = not users._fields["signature"].compute
        cls.users = []
        for name in ("Alice Sender", "Bruno Sender", "Carla Sender"):
            vals = {"name": name, "login": name.lower().replace(" ", ".")}
            if signature_is_stored:
                vals["signature"] = (
                    f"<table><tr><td><b>{name}</b></td></tr>"
                    "<tr><td>Compassion</td></tr></table>"
                )
            user = users.create(vals)
            if "hr.employee" in cls.env:
                # Signatures built from the employee data (name, job, photo)
                cls.env["hr.employee"].create(
                    {"name": name, "user_id": user.id, "job_title": "Tester"}
                )
            cls.users.append(user)
        cls.user_a, cls.user_b, cls.user_c = cls.users
        cls.partner = cls.env["res.partner"].create(
            {"name": "Signature Test Partner", "email": "sig@example.com"}
        )
        cls.config = cls.env.ref("partner_communication.default_communication")

    def _signature(self, user):
        return str(user.with_context(lang=self.partner.lang).signature)

    def _new_job(self):
        job = self.env["partner.communication.job"].create(
            {
                "config_id": self.config.id,
                "partner_id": self.partner.id,
                "object_ids": self.partner.id,
                "user_id": self.user_a.id,
                "send_mode": "digital",
            }
        )
        # Text generated from the template first, as for a real communication
        self.assertTrue(job.body_html)
        job.body_html = (
            "<p>Hello</p><p>Text written for the sponsor.</p>"
            f"<p>{self._signature(self.user_a)}</p>"
        )
        return job

    def test_signatures_differ(self):
        self.assertNotEqual(self._signature(self.user_a), self._signature(self.user_b))

    def test_sender_change_replaces_signature(self):
        job = self._new_job()
        job.user_id = self.user_b
        self.assertIn(self._signature(self.user_b), job.body_html)
        self.assertNotIn(self._signature(self.user_a), job.body_html)
        self.assertIn("Text written for the sponsor.", job.body_html)

    def test_sender_change_with_text_edited_in_editor(self):
        """The editor rewrites the HTML: the signature is found by its text."""
        job = self._new_job()
        edited = re.sub(
            r">\s*<",
            ">\n  <",
            str(job.body_html).replace(
                "<p>Hello</p>", '<p data-oe-version="1.2">Hi</p>'
            ),
        )
        self.assertNotIn(self._signature(self.user_a), edited)
        job.write({"user_id": self.user_b.id, "body_html": edited})
        self.assertIn("Hi", job.body_html)
        self.assertIn("Text written for the sponsor.", job.body_html)
        self.assertIn(self.user_b.name, job.body_html)
        self.assertNotIn(self.user_a.name, job.body_html)

    def test_signature_removed_by_hand_is_kept_removed(self):
        job = self._new_job()
        body = "<p>Hello</p><p>No signature here.</p>"
        job.body_html = body
        job.user_id = self.user_b
        self.assertEqual(job.body_html, body)

    def test_sender_change_in_form_updates_text_before_saving(self):
        job = self._new_job()
        with Form(job) as form:
            form.user_id = self.user_b
            self.assertIn(self.user_b.name, form.body_html)
            self.assertNotIn(self.user_a.name, form.body_html)
            # Several changes before saving: each one replaces the previous
            form.user_id = self.user_c
            self.assertIn(self.user_c.name, form.body_html)
            self.assertNotIn(self.user_b.name, form.body_html)
        self.assertEqual(job.user_id, self.user_c)
        self.assertIn(self.user_c.name, job.body_html)
        self.assertNotIn(self.user_a.name, job.body_html)
        self.assertNotIn(self.user_b.name, job.body_html)
        self.assertIn("Text written for the sponsor.", job.body_html)
