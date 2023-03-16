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
