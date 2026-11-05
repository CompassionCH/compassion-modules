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
from datetime import datetime
from io import BytesIO
from os import path
from unittest.mock import patch

from psycopg2 import OperationalError
from PyPDF2 import PdfFileWriter

from odoo import fields

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

    def test_overlay_source_pdf(self):
        """The pages of a source PDF are composed with the translation, and the
        translation never gets a box over them."""
        writer = PdfFileWriter()
        for _i in range(3):
            writer.addBlankPage(595, 842)
        pdf = BytesIO()
        writer.write(pdf)
        letter = self._create_letter()
        self.assertFalse(letter._prints_translation_on_pages())

        letter.overlay_source_pdf = base64.b64encode(pdf.getvalue())

        self.assertEqual(letter.overlay_source_nbr_pages, 3)
        self.assertEqual(len(letter.page_ids), 3)
        self.assertTrue(letter._prints_translation_on_pages())
        # A final PDF is kept as it is and wins over the source PDF
        letter.sponsor_letter_scan = letter.overlay_source_pdf
        self.assertFalse(letter._prints_translation_on_pages())
        letter.sponsor_letter_scan = False
        # The page of the source PDF is the image of the page
        self.assertTrue(letter.page_ids[0].fetch_image())
        # A page past the template pages has no text box over the source PDF
        template_pages = len(letter.template_id.page_ids)
        if template_pages < 3:
            self.assertFalse(letter.page_ids[2].template_id)

    def test_mark_email_read_keeps_first_read_date(self):
        letter = self._create_letter()
        self.assertFalse(letter.email_read)
        first_read = datetime(2026, 1, 1, 10, 0, 0)
        second_read = datetime(2026, 1, 1, 10, 0, 5)

        with patch.object(fields.Datetime, "now", return_value=first_read):
            letter.mark_email_read()
        self.assertEqual(letter.email_read, first_read)

        with patch.object(fields.Datetime, "now", return_value=second_read):
            letter.mark_email_read()
        self.assertEqual(letter.email_read, first_read)

    def test_set_email_read_works_for_the_public_user(self):
        """The fallback job runs as the user who queued it (public user)"""
        letter = self._create_letter()
        read_date = datetime(2026, 1, 1, 10, 0, 0)
        public_user = self.env.ref("base.public_user")

        letter.with_user(public_user)._set_email_read(read_date)

        self.assertEqual(letter.email_read, read_date)

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
