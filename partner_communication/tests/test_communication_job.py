##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)


class TestCommunicationJob(TransactionCase):
    def assertUTF8Equal(self, actual, expected):
        self.assertEqual(actual.encode("UTF-8"), expected.encode("UTF-8"))

    def _set_email_false(self):
        self.partner.email = False

    def _set_pref_both(self):
        self.partner.global_communication_delivery_preference = "both"

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].browse(self.ref("base.res_partner_2"))
        self.config = self.env["partner.communication.config"].browse(
            self.ref("partner_communication.default_communication")
        )

    def test_call(self):
        self.assertEqual(
            self.partner.global_communication_delivery_preference, "auto_digital"
        )
        self.partner.global_communication_delivery_preference = "none"
        self.assertEqual(self.partner.global_communication_delivery_preference, "none")

        comm = self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": self.config.id}
        )
        self.assertFalse(comm.send_mode)
        comm.send_mode = "digital"

        num_job = 1

        self.assertEqual(self.partner.communication_count, num_job)

        self.assertIn(comm.state, ["pending"])
        self.assertTrue(comm.send())
        self.assertEqual(self.partner.communication_count, num_job)
        self.assertIn(comm.state, ["done"])

        comm.reset()
        self.assertEqual(self.partner.communication_count, num_job)
        comm.cancel()
        self.assertEqual(self.partner.communication_count, num_job - 1)

        call_answer = comm.call()
        self.assertEqual(call_answer["context"]["phone_number"], "+32 10 588 558")
        self.assertEqual(call_answer["context"]["click2dial_id"], comm.id)

    def test_config(self):
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", True))
        # partner preference as job pref
        self.assertEqual(self.config.send_mode, "partner_preference")

        self.partner.global_communication_delivery_preference = "none"
        self.assertEqual(self.config.get_inform_mode(self.partner), (False, False))

        self.partner.global_communication_delivery_preference = "auto_digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", True))

        self.partner.global_communication_delivery_preference = "auto_physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", True))

        self.partner.global_communication_delivery_preference = "digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", False))

        self.partner.global_communication_delivery_preference = "physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))

        self.partner.global_communication_delivery_preference = "both"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("both", True))

        # Job where we prefer physical
        self.config.send_mode = "physical"
        self.assertEqual(self.config.send_mode, "physical")

        self.partner.global_communication_delivery_preference = "digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))

        self.partner.global_communication_delivery_preference = "both"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))

        # job pref == digital -> interesting for physical partner
        self.config.send_mode = "digital"
        self.assertEqual(self.config.send_mode, "digital")
        self.assertEqual(self.config.print_if_not_email, False)

        self.partner.global_communication_delivery_preference = "auto_digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", False))
        self.partner.global_communication_delivery_preference = "physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), (False, False))

        self.config.print_if_not_email = True
        self.partner.global_communication_delivery_preference = "physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))
        self.config.print_if_not_email = False

        self.partner.global_communication_delivery_preference = "both"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", False))

        # send_mode == both -> still no paper is email only
        self.config.send_mode = "both"
        self.assertEqual(self.config.send_mode, "both")

        self.partner.global_communication_delivery_preference = "auto_digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("both", True))

        self.partner.global_communication_delivery_preference = "physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))

        # user has no email field -> every digital should result in None
        self.partner.email = False
        self.config.send_mode = "digital"
        self.assertEqual(self.config.send_mode, "digital")
        self.assertEqual(self.config.print_if_not_email, False)

        self.partner.global_communication_delivery_preference = "auto_digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), (False, False))

        self.config.print_if_not_email = True
        self.assertEqual(self.config.print_if_not_email, True)
        self.partner.global_communication_delivery_preference = "digital"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("physical", False))

    def test_digital_only(self):
        # Some tests to check if digital only preference is well treated
        self.partner.global_communication_delivery_preference = "digital_only"
        self.config.send_mode = "physical"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", False))
        self.partner.global_communication_delivery_preference = "physical"
        self.config.send_mode = "digital_only"
        self.assertEqual(self.config.get_inform_mode(self.partner), ("digital", False))
        self.partner.email = False
        self.assertEqual(self.config.get_inform_mode(self.partner), (False, False))

    def test_multiple_jobs(self):
        non_default_config = self.env["partner.communication.config"].browse(
            self.ref("partner_communication.test_communication")
        )
        self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": non_default_config.id}
        )
        self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": self.config.id}
        )

        self.assertEqual(self.partner.communication_count, 2)

        # adding job to the same person with same config -> no new job
        self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": non_default_config.id}
        )
        # TODO check for other function like count page. For that you need
        # to add a report template to the config. It was not successful
        # until now.
        self.assertEqual(self.partner.communication_count, 2)

    def test_omr_generation(self):
        job = self.env["partner.communication.job"].create(
            {"partner_id": self.partner.id, "config_id": self.config.id}
        )
        marks = job._compute_marks(is_latest_page=True)
        self.assertListEqual(marks, [True, True, False, False, True, False, True])
        layer = job._build_omr_layer(marks)
        self.assertTrue(layer)
