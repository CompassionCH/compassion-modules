##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import logging
import os
from os import path
from unittest.mock import patch

from psycopg2 import OperationalError

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

logger = logging.getLogger(__name__)

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data/"


class TestSbcCompassion(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

        self.t_child = self.create_child("TT123456789")
        self.t_partner = self.env.ref("base.res_partner_address_31")
        t_group = self.create_group({"partner_id": self.t_partner.id})
        self.t_sponsorship = self.create_contract(
            {
                "partner_id": self.t_partner.id,
                "group_id": t_group.id,
                "child_id": self.t_child.id,
            },
            [{"amount": 50.0}],
        )

        self.list_files_path = [path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)]

        self.t_partner.write({"global_id": "12345678", "ref": "1231234"})

        self.waiting_sponsorship(self.t_sponsorship)
        self.t_sponsorship.force_activation()

    def test_base(self):
        self.assertEqual(self.t_sponsorship.child_id.local_id, "TT123456789")
        self.assertEqual(self.t_sponsorship.partner_id.global_id, "12345678")
        self.assertEqual(self.t_sponsorship.state, "active")

    def _create_letter(self):
        return self.env["correspondence"].create(
            {
                "sponsorship_id": self.t_sponsorship.id,
                "direction": "Beneficiary To Supporter",
                "original_text": "Hello",
            }
        )

    def test_mark_email_read_keeps_first_read_date(self):
        letter = self._create_letter()
        self.assertFalse(letter.email_read)

        letter.mark_email_read()
        first_read = letter.email_read
        self.assertTrue(first_read)

        letter.mark_email_read()
        self.assertEqual(letter.email_read, first_read)

    def test_mark_email_read_falls_back_to_a_job(self):
        letter = self._create_letter()
        letter_model = type(letter)

        with (
            patch.object(letter_model, "_set_email_read", side_effect=OperationalError),
            patch.object(letter_model, "with_delay_sh") as delayed,
        ):
            letter.mark_email_read()

        delayed.assert_called_once()
        self.assertEqual(delayed.call_args.args[0], "_set_email_read")
        self.assertFalse(letter.email_read)

    def test_import_pdf(self):
        """
        This test import the pdf include in the folder /data and verify the
        data's integrity.
        """
        list_data = []

        #  tuple with
        for file_path in self.list_files_path:
            with open(file_path, "rb") as f:
                list_data.append(
                    (
                        0,
                        False,
                        {
                            "name": f.name.split("/")[-1],
                            "datas": base64.b64encode(f.read()),
                        },
                    )
                )

        import_letter = (
            self.env["import.letters.history"]
            .with_context(queue_job__no_delay=True)
            .create({"data": list_data})
        )

        import_letter.button_import()
        self.assertEqual(len(import_letter.import_line_ids), 6)

        # Check the import line
        for line in import_letter.import_line_ids:
            if line.file_name.startswith("Dove"):
                self.assertEqual(line.template_id.name, "Dove")
                self.assertEqual(line.partner_id.name, "Addison Olson")
                self.assertEqual(line.child_id.display_name, "TT123456789")
            if line.file_name.startswith("Postman"):
                self.assertEqual(line.template_id.name, "Postman")
