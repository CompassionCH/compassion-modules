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

from odoo.tests import SingleTransactionCase


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
