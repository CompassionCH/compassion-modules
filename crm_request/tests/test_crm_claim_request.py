##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <guernej@compassion.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from odoo.tests import Form, SingleTransactionCase


class TestCrmClaimCategories(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_request_creation(self):
        msg = {
            "date": datetime.now(),
            "subject": "this is a subject",
            "from": "test@test.ch",
            "body": "hello",
            "to": "other@mail.com",
        }

        # create a claim with a message dictionary
        self.env["crm.claim"].message_new(msg)

        # create a claim with no subject (CO-3684)
        msg.pop("subject")
        self.env["crm.claim"].message_new(msg)

    def test_request_default_stage_is_new(self):
        """A request created without a stage starts in "New", even when
        another stage has sequence 1 after the stages were reordered (T1937)."""
        stage_new = self.env.ref("crm_claim.stage_claim1")
        other_stage = self.env["crm.claim.stage"].create(
            {"name": "Internal requests", "case_default": True, "sequence": 1}
        )
        stage_new.sequence = 0

        request = self.env["crm.claim"].create({"name": "From a website form"})
        self.assertEqual(request.stage_id, stage_new)

        # An explicit stage, like the one set by an email alias, is kept
        request = self.env["crm.claim"].create(
            {"name": "Internal request", "stage_id": other_stage.id}
        )
        self.assertEqual(request.stage_id, other_stage)
        request = (
            self.env["crm.claim"]
            .with_context(default_stage_id=other_stage.id)
            .create({"name": "Internal request"})
        )
        self.assertEqual(request.stage_id, other_stage)

    def test_reply_uses_category_template(self):
        """Reply shows the category's template answer above the quoted
        message (T3547)."""
        partner = self.env["res.partner"].create(
            {"name": "T3547 Requester", "email": "t3547@example.org", "lang": "en_US"}
        )
        template = self.env["mail.template"].create(
            {
                "name": "T3547 answer",
                "model_id": self.env.ref("crm_claim.model_crm_claim").id,
                "body_html": "<p>Template answer to <t t-out='object.name'/></p>",
            }
        )
        category = self.env["crm.claim.category"].create(
            {"name": "T3547 category", "template_id": template.id}
        )
        request = self.env["crm.claim"].create(
            {
                "name": "T3547 question",
                "partner_id": partner.id,
                "language": "en_US",
                "categ_id": category.id,
            }
        )
        request.message_post(
            body="Where is my letter?", author_id=partner.id, message_type="email"
        )

        composer = Form(
            self.env["mail.compose.message"].with_context(
                **request.action_reply()["context"]
            )
        )
        body = str(composer.body)
        self.assertIn("Template answer to T3547 question", body)
        self.assertIn("Where is my letter?", body)
        self.assertLess(
            body.index("Template answer"), body.index("Where is my letter?")
        )

        # Without a template, the reply keeps the greeting and the quote
        category.template_id = False
        composer = Form(
            self.env["mail.compose.message"].with_context(
                **request.action_reply()["context"]
            )
        )
        self.assertNotIn("Template answer", str(composer.body))
        self.assertIn("Where is my letter?", str(composer.body))

    def test_reply_template_in_request_language(self):
        """The template answer is rendered in the request's language, not in
        the language of the staff member who replies (T3547)."""
        self.env["res.lang"]._activate_lang("de_DE")
        partner = self.env["res.partner"].create(
            {"name": "T3547 German requester", "email": "t3547-de@example.org"}
        )
        template = self.env["mail.template"].create(
            {
                "name": "T3547 translated answer",
                "model_id": self.env.ref("crm_claim.model_crm_claim").id,
                "lang": "{{ object.env.context.get('salutation_language') }}",
                "body_html": "<p>Answer in English</p>",
            }
        )
        template.with_context(lang="de_DE").body_html = "<p>Antwort auf Deutsch</p>"
        category = self.env["crm.claim.category"].create(
            {"name": "T3547 translated category", "template_id": template.id}
        )
        request = self.env["crm.claim"].create(
            {
                "name": "T3547 Frage",
                "partner_id": partner.id,
                "language": "de_DE",
                "categ_id": category.id,
            }
        )

        body = str(
            request.with_context(lang="en_US").action_reply()["context"]["default_body"]
        )
        self.assertIn("Antwort auf Deutsch", body)
        self.assertNotIn("Answer in English", body)
